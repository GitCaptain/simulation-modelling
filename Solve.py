from matplotlib import pyplot
import csv
from SALib.sample import saltelli
from SALib.analyze import sobol
import numpy as np
import multiprocessing
import os


class AbstractPlot:
    def __init__(self, plot_name="", xname="", yname=""):
        self.title = plot_name
        self.xname = xname
        self.yname = yname
        self.plots = []
        self.plot = pyplot
        self.clear()
        self.plot.title(self.title)
        self.plot.xlabel(self.xname)
        self.plot.ylabel(self.yname)

    def add(self, x, y, label=""):
        self.plots.append((x, y, label))

    def restore(self):
        self.clear()
        self.plot.title(self.title)
        self.plot.xlabel(self.xname)
        self.plot.ylabel(self.yname)

    def show(self):
        self.plot.legend()
        self.plot.show()
        self.restore()

    def save(self, name):
        self.plot.legend()
        self.plot.savefig(name)

    def clear(self):
        self.plot.clf()


class Plot(AbstractPlot):
    def __init__(self, plot_name="", xname="", yname=""):
        super().__init__(plot_name, xname, yname)

    def add(self, x, y, label=""):
        super().add(x, y, label)
        self.plot.plot(x, y, label=label)

    def restore(self):
        super().restore()
        for plt in self.plots:
            self.plot.plot(plt[0], plt[1], label=plt[2])


class Scatter(AbstractPlot):
    def __init__(self, plot_name="", xname="", yname=""):
        super().__init__(plot_name, xname, yname)

    def add(self, x, y, label=""):
        super().add(x, y, label)
        self.plot.scatter(x, y, label=label)

    def restore(self):
        super().restore()
        for plt in self.plots:
            self.plot.scatter(plt[0], plt[1], label=plt[2])


class Solver:
    def __init__(self):
        self.rf_code = '643'
        self.females_file = "females_2005.csv"
        self.males_file = "males_2005.csv"
        self.both_file = "both.csv"

    @staticmethod
    def process_survival_data(processing_year_previous, processing_year_current, do_round=True):
        coefficients = [1]
        ages = [0]
        for i in range(1, len(processing_year_current)):
            if processing_year_current[i] > processing_year_previous[i - 1]:
                # kind of error in data, just take previous result
                coefficients.append(coefficients[-1])
            else:
                coefficients.append(processing_year_current[i] / processing_year_previous[i - 1])
            ages.append(ages[-1] + 5)
        if do_round:
            coefficients = list(map(lambda x: round(x, 3), coefficients))
        return ages, coefficients

    @staticmethod
    def get_row(file, country_code, year):
        with open(file, newline='') as csv_file:
            reader = csv.reader(csv_file, delimiter=';')
            for row in reader:
                if row[4] == country_code and row[5] == year:
                    return list(map(lambda x: int(float(x.replace(',', '')
                                                    if x != '-'
                                                    else 0) * 1000),
                                    row[6:]))

    def prognosis(self, target_year, fertility, birth_rate, *survival_rates):
        group_cnt = 5

        survival_man = survival_rates[:len(survival_rates)//2]
        survival_women = survival_rates[len(survival_rates)//2:]

        def get_women_cnt(all_people):
            return birth_rate * all_people / (birth_rate + 1)

        def get_man_cnt(all_people):
            return all_people - get_women_cnt(all_people)

        def recalc_people(all_people, age):
            return int(get_man_cnt(all_people) * survival_man[age // group_cnt] +
                       get_women_cnt(all_people) * survival_women[age // group_cnt])

        people_2005 = self.get_row(self.both_file, self.rf_code, '2005')

        assert target_year > 2005, "modelling year should be greater than 2005"

        years = range(2006, target_year)
        fertility_start = 20
        fertility_end = 40
        prognosis_people = [people_2005]
        age_groups = range(5, 106, 5)
        for _ in years:
            previous_year = prognosis_people[-1]
            current_year_prognosis = [0]
            for i, age in enumerate(age_groups):
                current_year_prognosis.append(recalc_people(previous_year[i], age))

            current_year_prognosis[0] = int(get_women_cnt(
                sum(current_year_prognosis[fertility_start:fertility_end])
            ) * fertility)
            prognosis_people.append(current_year_prognosis)

        prognosis_people.pop(0)  # exclude 2005 people

        return prognosis_people

    def sensitive_analysys(self):

        def evaluate_mp(param_values, year):
            with multiprocessing.Pool() as p:
                chunk_size, extra = divmod(len(param_values), cpu_cnt)  # let each processor calc ~ equal data size
                if extra:
                    chunk_size += 1
                Y = p.starmap(self.prognosis, map(lambda x: (year, *x), param_values), chunk_size)
                return np.array(Y)

        # Define the model inputs
        man_survivals = []
        women_survivals = []
        for age_group in range(0, 106, 5):
            man_survivals.append(f"survival_man_{age_group}")
            women_survivals.append(f"survival_woman_{age_group}")

        problem = {
            'num_vars': 2 + len(man_survivals) + len(women_survivals),
            'names': ['fertility', 'birth_rate', *man_survivals, *women_survivals],
            'bounds': [[1.1, 2.5],  # smallest and biggest fertility in russia (1960 - 2017)
                       [0.5, 2],  # assume that one gender cannot outnumber another more than twice
                       *[[0, 1] for _ in range(len(women_survivals) + len(man_survivals))]  # logical bounds to survival rate
                       ]
        }

        # Generate samples
        print("generating samples...")
        sample_count = 1000
        param_values = saltelli.sample(problem, sample_count)
        print("generation done.")

        # import time
        # def evaluate(param_values, year):
        #     Y = []
        #     for params in param_values:
        #         Y.append(self.prognosis(year, *params))
        #     return np.array(Y)
        # cpu_cnt = os.cpu_count()
        # for f in evaluate, evaluate_mp:
        #     """
        #     evaluate evaluate...
        #     calc time: 510.3338315486908 sec
        #     evaluate evaluate_mp...
        #     calc time: 139.08048725128174 sec
        #     """
        #     print(f"evaluate {f.__name__}...")
        #     start = time.time()
        #     Y = f(param_values, 2015)
        #     all = time.time() - start
        #     del Y
        #     print(f"calc time: {all} sec")

        # Run model (example)
        test_years = [2015, 2025, 2055, 2105]
        cpu_cnt = os.cpu_count()
        print(f"using {cpu_cnt} processors")
        for year in test_years:
            print(f"processing year: {year}")
            print("start evaluation")
            Y = evaluate_mp(param_values, year).flatten()
            # Perform analysis
            print("start analysis")
            Si = sobol.analyze(problem, Y, print_to_console=False)
            print(f"{year} result: ")
            # Print the first-order sensitivity indices
            print(Si['S1'])

    def determine_ranges(self):
        pass

    def uncertainty_analysis(self):
        pass

    def solve(self):
        solve_order = (self.sensitive_analysys, self.determine_ranges, self.uncertainty_analysis)
        for method in solve_order:
            print(f"processing: {method.__name__} ...")
            method()


if __name__ == '__main__':
    from pathlib import Path
    Path("./results").mkdir(parents=True, exist_ok=True)
    s = Solver()
    s.solve()
