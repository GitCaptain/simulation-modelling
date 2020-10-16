from matplotlib import pyplot
import csv


class Plot:
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
        self.plot.plot(x, y, label=label)

    def restore(self):
        self.clear()
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

    def clear(self):
        self.plot.clf()


class Solver:
    def __init__(self):
        self.rf_code = '643'
        self.females_file = "females_2005.csv"
        self.males_file = "males_2005.csv"
        self.both_file = "both.csv"

    @staticmethod
    def process_data(processing_year_previous, processing_year_current, do_round=True):
        coefficients = [1]
        ages = [0]
        for i in range(1, len(processing_year_current)):
            if processing_year_current[i] > processing_year_previous[i - 1]:
                # kind of error in data, just take previous result
                coefficients.append(coefficients[-1])
            else:
                coefficients.append(processing_year_current[i] / processing_year_previous[i - 1])
            if do_round:
                coefficients = list(map(lambda x: round(x, 3), coefficients))
            ages.append(ages[-1] + 5)
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

    def survival_rate(self, do_plot=True, do_round=True):
        year = '2005'
        previous_year = '2000'
        females_2000 = self.get_row(self.females_file, self.rf_code, previous_year)
        females_2005 = self.get_row(self.females_file, self.rf_code, year)
        males_2000 = self.get_row(self.males_file, self.rf_code, previous_year)
        males_2005 = self.get_row(self.males_file, self.rf_code, year)
        plot = Plot("survival rate", "age", "coeff")

        ages, males_survival_2005 = self.process_data(males_2005, males_2000, do_round)
        ages, females_survival_2005 = self.process_data(females_2005, females_2000, do_round)

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
        # and so on: 10, 15 years ago and also in future: +5, +10, +15 years
        # so we can count fertility starting from 1965 to 1990
        females_cnt = []
        fertility_years = range(1965, 1990, 5)
        births = [0 for _ in range(len(fertility_years))]
        years = []
        for i, fertility_year in enumerate(fertility_years):
            years.append(fertility_year)
            # sum of women in all included categories
            females_cnt.append(sum(self.get_row(self.females_file, self.rf_code, str(fertility_year))[4:8]))
            first_in = 4  # first included group: 20-24 years (same for all years)
            last_in = 5  # the group after last included: changes every step
            for included_year in range(fertility_year - 15, fertility_year + 5, 5):
                births[i] += self.get_row(self.both_file, self.rf_code, str(included_year))[0] \
                             * (last_in - first_in) / 4
                last_in += 1
            first_in = 5
            last_in = 8
            for included_year in range(fertility_year + 5, fertility_year + 15, 5):
                births[i] += self.get_row(self.both_file, self.rf_code, str(included_year))[0] \
                             * (last_in - first_in) / 4
                first_in += 1

        print(females_cnt)
        print(births)
        fertility = [x / y for x, y in zip(births, females_cnt)]
        if do_plot:
            plot = Plot("fertility rate", "years", "rate")
            plot.add(years, fertility)
            plot.show()
            plot.save("results/fertility_rate.png")
        return fertility

    def birth_rate(self, do_plot=True):
        females_birth = []
        males_birth = []
        both_birth = []
        years = []
        for year in range(1950, 2010, 5):
            females_birth.append(self.get_row(self.females_file, self.rf_code, str(year))[0])
            males_birth.append(self.get_row(self.males_file, self.rf_code, str(year))[0])
            both_birth.append(self.get_row(self.both_file, self.rf_code, str(year))[0])
            years.append(year)
        # print(females_birth)
        # print(males_birth)
        get_rate = lambda l1, l2: [x / y for x, y in zip(l1, l2)]
        birth_rate = get_rate(males_birth, females_birth)
        if do_plot:
            plot = Plot("birth rate", "year", "males/females")
            plot.add(years, birth_rate)
            plot.save("results/birth_rate.png")
            # del plot
            # plot = Plot("birth rate", "year", "rate")
            # plot.add(years, get_rate(males_birth, both_birth), "males/both")
            # plot.add(years, get_rate(females_birth, both_birth), "females/both")
            # plot.show()
        return birth_rate

    def convert_coef(self):
        convert = lambda lst: [x ** 0.2 for x in lst]
        fertility = convert(self.fertility_rate(False))
        # print(f"fertility coef:\n{fertility}")
        survival = self.survival_rate(do_plot=False, do_round=False)
        survival_man = convert(survival[1])
        survival_women = convert(survival[2])
        birth_rate = convert(self.birth_rate(False))
        # print(f"survival:\nman: {survival_man}\nwomen: {survival_women}")
        return fertility[-1], birth_rate[-1], survival_man, survival_women

    def prognosis(self, do_plot=True):
        fertility, birth_rate, survival_man, survival_women = self.convert_coef()
        print(f"fertility: {fertility}\nbirth: {birth_rate}\nman: {survival_man}\nwomen: {survival_women}")
        prognose_people = [list(map(lambda x: int(x/5), self.get_row(self.both_file, self.rf_code, '2005')))]
        get_women_cnt = lambda all_people: birth_rate * all_people / (birth_rate + 1)
        get_man_cnt = lambda all_people: all_people - get_women_cnt(all_people)
        ages = range(5, 105, 5)
        years = range(2006, 2106)
        for _ in years:
            previous_year = prognose_people[-1]
            current_year_prognose = [0]
            for i, age in enumerate(ages):
                previous_year_people_previous_age = previous_year[age // 5 - 1]
                current_year_prognose.append(int(
                    get_man_cnt(previous_year_people_previous_age) * survival_man[i] +
                    get_women_cnt(previous_year_people_previous_age) * survival_women[i]
                ))
            current_year_prognose[0] = int(get_women_cnt(sum(current_year_prognose[4:8])) * fertility)
            prognose_people.append(current_year_prognose)

        if do_plot:
            plot = Plot("russian population", "years", "people count")
            plot.add(years, [sum(x) for x in prognose_people[1:]])
            plot.save("results/population100.png")
            plot.show()
            del plot

            plot = Plot("survival rates", "ages", "people")
            rates = []
            for i in range(1, len(prognose_people)):
                rates.append(self.process_data(prognose_people[i - 1], prognose_people[i]))

            for i, year in enumerate(years):
                if i % 10:
                    continue
                plot.add(*rates[i], f"people {year}")
            plot.save("results/survival_rate_prognose.png")
            plot.show()
        return prognose_people

    def solve(self):
        solve_order = (self.survival_rate, self.fertility_rate, self.birth_rate, self.convert_coef, self.prognosis)
        for method in solve_order:
            print(f"processing: {method.__name__} ...")
            method()


if __name__ == '__main__':
    s = Solver()
    s.solve()
