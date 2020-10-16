from matplotlib import pyplot
import csv


class Plot:
    def __init__(self, plot_name="", xname="", yname=""):
        self.title = plot_name
        self.xname = xname
        self.yname = yname
        self.plots = []
        self.plot = pyplot
        self.plot.clf()
        self.plot.title(self.title)
        self.plot.xlabel(self.xname)
        self.plot.ylabel(self.yname)

    def add(self, x, y, label=""):
        self.plots.append((x, y, label))
        self.plot.plot(x, y, label=label)

    def restore(self):
        self.plot.clf()
        self.plot.title(self.title)
        self.plot.xlabel(self.xname)
        self.plot.ylabel(self.yname)
        for plt in self.plots:
            self.plot.plot(plt[0], plt[1], label=plt[2])

    def show(self):
        self.plot.legend()
        self.plot.show()
        self.restore()

    def save(self, name):
        self.plot.legend()
        self.plot.savefig(name)


def get_row(file, country_code, year):
    with open(file, newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=';')
        for row in reader:
            if row[4] == country_code and row[5] == year:
                return list(map(lambda x: float(x.replace(',', '.')
                                                if x != '-'
                                                else 0) * 1000,
                                row[6:]))


class Solver:
    def __init__(self):
        self.rf_code = '643'
        self.females_file = "females_2005.csv"
        self.males_file = "males_2005.csv"
        self.both_file = "both.csv"

    def survival_rate(self, do_plot=True, do_round=True):

        def process_data(processing_year_2000, processing_year_2005, do_round=True):
            coefficients = [1]
            ages = [0]
            for i in range(1, len(processing_year_2005)):
                coefficients.append(processing_year_2005[i] / processing_year_2000[i - 1])
                if do_round:
                    coefficients = list(map(lambda x: round(x, 3), coefficients))
                ages.append(ages[i - 1] + 5)
            return ages, coefficients

        year_2005 = '2005'
        year_2000 = '2000'
        females_2005 = get_row(self.females_file, self.rf_code, year_2005)
        females_2000 = get_row(self.females_file, self.rf_code, year_2000)
        males_2005 = get_row(self.males_file, self.rf_code, year_2005)
        males_2000 = get_row(self.males_file, self.rf_code, year_2000)
        plot = Plot("survival rate", "age", "coeff")
        ages, males_survival_2005 = process_data(males_2000, males_2005, do_round)
        ages, females_survival_2005 = process_data(females_2000, females_2005, do_round)
        if do_plot:
            plot.add(ages, females_survival_2005, "females rate")
            plot.add(ages, males_survival_2005, "males rate")
            # plot.show()
            plot.save("results/survival_rate.png")
        return ages, males_survival_2005, females_survival_2005

    def fertility_rate(self, do_plot=True):
        # count fertility for woman in year 2005
        # there are 4 woman categories:
        # 1: 20-24, 2: 25-29, 3: 30-34, 4: 35-39 (in csv file group number shifts by 3: 1-4 -> 4-7)
        # 5 years ago 2, 3, 4 woman categories was in 1, 2, 3
        # and give about 3/4 of births, so we need to count it too
        # and so on: 10, 15 years ago
        # so we can count fertility starting from 1965
        females_cnt = []
        births = [0 for _ in range(9)]
        years = []
        for i, fertility_year in enumerate(range(1965, 2010, 5)):
            first_in = 4  # first included group: 20-24 years (same for all years)
            last_in = 5  # the group after last included: changes every step
            years.append(fertility_year)
            # sum of women in all included categories
            females_cnt.append(sum(get_row(self.females_file, self.rf_code, str(fertility_year))[4:8]))
            for included_year in range(fertility_year - 15, fertility_year + 5, 5):
                births[i] += get_row(self.both_file, self.rf_code, str(included_year))[0] * (last_in - first_in) / 4
                last_in += 1

        print(females_cnt)
        print(births)
        fertility = [y / x for x, y in zip(females_cnt, births)]
        if do_plot:
            plot = Plot("fertility rate", "years", "rate")
            plot.add(years, fertility)
            plot.show()
            plot.save("results/fertility_rate.png")
        return fertility

    def birth_rate(self, do_plot=True):
        females_birth = []
        males_birth = []
        years = []
        for year in range(1950, 2010, 5):
            females_birth.append(get_row(self.females_file, self.rf_code, str(year))[0])
            males_birth.append(get_row(self.males_file, self.rf_code, str(year))[0])
            years.append(year)
        print(females_birth)
        print(males_birth)
        birth_rate = [x / y for x, y in zip(males_birth, females_birth)]
        if do_plot:
            plot = Plot("birth rate", "year", "males/females")
            plot.add(years, birth_rate)
            # plot.show()
            plot.save("results/birth_rate.png")
        return birth_rate

    def convert_coef(self):
        convert = lambda lst: [x ** 0.2 for x in lst]
        fertility = convert(self.fertility_rate(False))
        print(f"fertility coef:\n{fertility}")
        survival = self.survival_rate(False, False)
        survival_man = convert(survival[1])
        survival_women = convert(survival[2])
        print(f"survival:\nman: {survival_man}\nwomen: {survival_women}")
        return fertility[-1], survival_man[-1], survival_women[-1]

    def prognosis(self):
        fertility, survival_man, survival_women = self.convert_coef()
        birth_rate = self.birth_rate(False)[-1]
        prognose_people = [get_row(self.both_file, self.rf_code, '2005')]

        get_women_cnt = lambda all_people: birth_rate * all_people / (birth_rate + 1)
        get_man_cnt = lambda all_people: all_people - get_women_cnt(all_people)

        for year in range(2006, 2106):
            previous_year = prognose_people[-1]
            current_year_prognose = [0]
            for age in range(5, 105, 5):
                previous_year_people_previous_age = previous_year[age//5-1]
                current_year_prognose.append(
                    get_man_cnt(previous_year_people_previous_age) * survival_man +
                    get_women_cnt(previous_year_people_previous_age) * survival_women
                )
            current_year_prognose[0] = get_women_cnt(sum(current_year_prognose[4:8]))*fertility
            prognose_people.append(current_year_prognose)

        return prognose_people

    def solve(self):
        solve_order = (self.survival_rate, self.fertility_rate, self.birth_rate, self.convert_coef, self.prognosis)
        for method in solve_order:
            print(f"processing: {method.__name__} ...")
            method()


if __name__ == '__main__':
    s = Solver()
    s.solve()
