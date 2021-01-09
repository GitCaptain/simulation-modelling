import sys
from queue import Queue, PriorityQueue
import random
from enum import IntEnum, Enum


class systemType(IntEnum):
    FIRST_TYPE  = 0
    SECOND_TYPE = 1
    THIRD_TYPE  = 2
    FOURTH_TYPE = 3


class eventType(IntEnum):
    CLIENT_ARRIVAL = 0
    # CLIENT_LEAVE = 1
    SERVER_READY = 2

    # four type system only
    # QUEUE_TOO_LONG = 3
    # QUEUE_TOO_SHORT = 4


class Server:

    def __init__(self, min_srv=1, max_srv=5):
        self.min_srv = min_srv
        self.max_srv = max_srv
        self.add_time = None
        self.serve_time = None

    def add(self, time):
        self.add_time = time
        self.serve_time = random.randint(self.min_srv, self.max_srv)
        return self.get_free_time()

    def is_free(self, time):
        return self.get_free_time() <= time

    def get_free_time(self):
        if self.add_time is None or self.serve_time is None:
            return 0
        return self.add_time + self.serve_time + 1

    def clear_state(self):
        self.add_time = None
        self.serve_time = None


class EventQueue:

    def __init__(self):
        self.queue = PriorityQueue()

    def add_event(self, event_time, event):
        self.queue.put((event_time, event))

    def get_event(self):
        if self.queue.empty():
            return None, None
        return self.queue.get()


class Statistics:

    class Metric:
        def __init__(self, name, initial_value=0, lower_is_better=True):
            self.name = name
            self.lib = lower_is_better
            self.value = initial_value

        def __add__(self, other):
            self.value += other

    class MetricsEnum(Enum):
        average_waiting_time = 0
        waiting_probability = 1
        clients_served = 2

    def __init__(self):
        self.average_waiting_time = self.Metric(self.MetricsEnum.average_waiting_time)
        self.waiting_probability = self.Metric(self.MetricsEnum.waiting_probability)
        self.clients_served = self.Metric(self.MetricsEnum.clients_served, 0, False)

    @staticmethod
    def compare_statistics(statistic_list):
        title = "system type | " + " | ".join([metric.name for metric in Statistics.MetricsEnum]) + "\n"
        sep = '-' * len(title) + "\n"
        table = sep + title + sep

        best = [[None, None, None] for _ in Statistics.MetricsEnum]

        for system_type in systemType:
            stat = statistic_list[system_type.value]
            awt = stat.average_waiting_time
            wp = stat.waiting_probability
            cs = stat.clients_served
            row = system_type.name + " " + \
                  str(awt.value) + " " +\
                  str(wp.value) + " " +\
                  str(cs.value) + "\n"

            Sawt = Statistics.MetricsEnum.average_waiting_time
            Swp = Statistics.MetricsEnum.waiting_probability
            Scs = Statistics.MetricsEnum.clients_served
            for pair in ((awt, Sawt), (wp, Swp), (cs, Scs)):
                possible, cur = pair
                if best[cur.value][0] is None or possible.value < best[cur.value][0]:
                    best[cur.value][0] = possible.value
                    best[cur.value][1] = possible.name
                    best[cur.value][2] = system_type.name

            table += row + sep

        table += "Best:\n" + "\n".join([" ".join([str(x) for x in y]) for y in best])

        return table


def modelling(system_type, time_limit, servers, arrivals, threshold=None):

    statistic = Statistics()
    event_queue = EventQueue()
    global_time = 0  # seconds

    if system_type in (systemType.FIRST_TYPE, systemType.SECOND_TYPE):
        server_list = [Server() for _ in range(servers)]
        queue_list = [Queue() for _ in range(servers)]  # each server has a queue
    elif system_type == systemType.THIRD_TYPE:
        server_list = [Server() for _ in range(servers)]
        queue_list = [Queue()]
    else: # FOURTH_TYPE
        queue_list = [Queue()]
        server_list = []

    for arrival in arrivals:
        event_queue.add_event(arrival, eventType.CLIENT_ARRIVAL)

    def update(queue, server):
        q_time = queue.get()
        free_time = server.add(q_time)
        event_queue.add_event(free_time, eventType.SERVER_READY)
        statistic.average_waiting_time.value += global_time - q_time
        statistic.waiting_probability.value += (global_time != q_time)
        if server.add_time is not None:
            statistic.clients_served.value += 1

    while True:
        e_time, e_type = event_queue.get_event()

        if e_type is None or e_time > time_limit:
            # events are over or time limit reached
            break

        global_time = e_time

        if system_type in (systemType.FIRST_TYPE, systemType.SECOND_TYPE):

            if e_type == eventType.CLIENT_ARRIVAL:
                if system_type == systemType.FIRST_TYPE:
                    client_queue = random.randint(0, len(queue_list)-1)
                    queue_list[client_queue].put(e_time)

                if system_type == systemType.SECOND_TYPE:
                    sorted(queue_list, key=lambda q: q.qsize())[0].put(e_time)

            for queue, server in zip(queue_list, server_list):
                if server.is_free(global_time) and not queue.empty():
                    update(queue, server)

        if system_type in (systemType.THIRD_TYPE, systemType.FOURTH_TYPE):

            queue = queue_list[0]
            if e_type == eventType.CLIENT_ARRIVAL:
                queue.put(e_time)

            if system_type == systemType.FOURTH_TYPE:
                if queue.qsize() > threshold[1]:
                    server_list.append(Server())

            for server in filter(lambda server: server.is_free(global_time), server_list):
                if not queue.empty():
                    update(queue, server)
                else:
                    break

            if system_type == systemType.FOURTH_TYPE:
                if queue.qsize() < threshold[0]:
                    # remove all free servers
                    server_list = list(filter(lambda server: not server.is_free(global_time), server_list))

    statistic.average_waiting_time.value /= len(arrivals)
    statistic.waiting_probability.value /= len(arrivals)

    return statistic


def main():
    """
    sys.argv: modelling time, number of server, arrival rate, queue threshold min and max
    :return:
    """

    modelling_time = 10000  # in seconds
    number_of_servers = 10
    arrival_rate = 3.33  # person per second
    threshold_mn = 3  # min people in queue (del server)
    threshold_mx = 7  # max people in queue (add server)
    if len(sys.argv) == 6:
        modelling_time = int(sys.argv[1])
        number_of_servers = int(sys.argv[2])
        arrival_rate = float(sys.argv[3])
        threshold_mn = int(sys.argv[4])
        threshold_mx = int(sys.argv[5])
    else:
        print("using default values for modelling")

    # use same arrival events for all queues
    # round arrival_probability_per_second to nearest upper integer,
    # to have more than one person at time if probability is high
    client_arrival_times = []
    times = round(arrival_rate + 0.5)
    per_times_probability = arrival_rate/times
    for t in range(modelling_time):
        for _ in range(times):
            r = random.random()
            if r < per_times_probability:
                client_arrival_times.append(t)

    statistics = [None for _ in systemType]

    for s_type in systemType:
        s = modelling(s_type,
                      modelling_time,
                      number_of_servers,
                      client_arrival_times,
                      (threshold_mn, threshold_mx) if s_type == systemType.FOURTH_TYPE else None)
        statistics[s_type.value] = s

    print(Statistics.compare_statistics(statistics))


if __name__ == '__main__':
    main()
