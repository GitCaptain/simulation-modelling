import sys
from queue import Queue, PriorityQueue
import random
from enum import IntEnum


class systemType(IntEnum):
    FIRST_TYPE  = 1
    SECOND_TYPE = 2
    THIRD_TYPE  = 3
    FOURTH_TYPE = 4


class eventType(IntEnum):
    CLIENT_ARRIVAL = 0
    CLIENT_LEAVE = 1
    SERVER_READY = 2

    # four type system only
    QUEUE_TOO_LONG = 3
    QUEUE_TOO_SHORT = 4


class Server:

    def __init__(self, min_srv=1, max_srv=5):
        self.min_srv = min_srv
        self.max_srv = max_srv
        self.add_time = None
        self.serve_time = None

    def add(self, time):
        self.add_time = time
        self.serve_time = random.randint(self.max_srv, self.max_srv)

    def get_free_time(self):
        if not self.add_time:
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
            return None
        return self.queue.get()[1]


class Statistics:
    pass


def modelling(type, time, servers, arrival, threshold=None):

    s = Statistics()
    eq = EventQueue()
    arrival_times = random.randrange()
    if type != systemType.FOURTH_TYPE:
        server_list = [Server() for _ in range(servers)]
        queue_list = [Queue() for _ in range(servers)]  # each server has a queue
    else:
        queue_list = [Queue()]
        server_list = []

    while True:
        e = eq.get_event()

        if not e:
            break

        for s_id, server in enumerate(server_list):
            eq.add_event(server.get_free_time(), (eventType.SERVER_READY, s_id))

        for q_id, queue in enumerate(queue_list):
            if queue.qsize() < threshold[0]:
                eq.add_event(())

    return s


def main():
    """
    sys.argv: modelling time, number of server, arrival rate, queue threshold min and max
    :return:
    """
    modelling_time = 100  # in minutes
    number_of_servers = 5
    arrival_rate = 2/1  # person per minute
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

    statistics = []
    for s_type in systemType:
        s = modelling(s_type,
                      modelling_time,
                      number_of_servers,
                      arrival_rate,
                      (threshold_mn, threshold_mx) if s_type == systemType.FOURTH_TYPE else None)
        statistics.append((s, s_type))


if __name__ == '__main__':
    # a = EventQueue(10, 10)
    # a.add_event(5, 3)
    # a.add_event(50, 3)
    # a.add_event(10, 3)
    # a.add_event(0, 3)
    # while True:
    #     e = a.get_event()
    #     if not e:
    #         break
    #     print(e)
    main()
