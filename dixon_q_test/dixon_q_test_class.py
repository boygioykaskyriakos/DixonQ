import pandas as pd

from copy import copy

from base_class.base_class_analytic import BaseClassAnalytic
from static_files.standard_variable_names import DATA_TYPE, NODE, VALUES, VALUE, KEY, \
    OUTLIER_NO, SUBSET, SUBSET_SIZE, INDEX_FIRST_ELEMENT, INDEX_LAST_ELEMENT, CONFIDENCE_LVL


class FindOutlierDixon(BaseClassAnalytic):
    def __init__(self, grouped_data: pd.DataFrame):
        BaseClassAnalytic.__init__(self)

        self.grouped_data = grouped_data
        self.static_n = self.read_ini_file_obj.get_int("DIXON_Q_TEST_SUBSET_VARIABLES", "static_n")
        self.static_n_maximum = self.read_ini_file_obj.get_int("DIXON_Q_TEST_SUBSET_VARIABLES", "static_n_maximum")
        self.counter = 0
        self.result = []

    @staticmethod
    def get_result(numbers: pd.Series, comparator: float) -> bool:
        numbers = copy(numbers).sort_values().to_list()

        q_lower = 0
        q_upper = 0
        denominator = float(numbers[-1]-numbers[0])

        if denominator > 0:
            q_lower = float(numbers[1] - numbers[0]) / denominator
            q_upper = float(numbers[-1] - numbers[-2]) / denominator

        if q_lower > comparator or q_upper > comparator:
            return True
        else:
            return False

    @staticmethod
    def find_comparator(numbers: list, confidence: tuple) -> float:
        get_number = len(numbers) - 3

        return confidence[get_number]

    def print_to_console(self, static_n: int, confidence_lvl: str,
                         whole_set: pd.DataFrame, temp_data: pd.Series, i: int) -> None:

        msg = "*************************************************************************************" + "\n"
        msg += "OUTLIER FOUND No " + str(self.counter) + "\n"
        msg += "SUBSET SIZE IS " + str(static_n) + "\n"
        msg += "NODE IS " + str(whole_set[NODE].values[0]).replace("\t", "") + \
               " AND DATA TYPE IS " + whole_set[DATA_TYPE].values[0] + "\n"
        msg += "FIRST ELEMENT INDEX IS " + str(i) + " AND LAST ELEMENT INDEX IS " + str(static_n + i-1) + "\n"
        msg += "THE SUB SET IS: " + "\n"
        msg += str(temp_data.tolist()) + " " + "\n"
        msg += "WITH " + str(confidence_lvl).upper() + "\n"
        msg += "*************************************************************************************"

        print(msg)

    def results_to_list(
            self, static_n: int, confidence_lvl: str,
            whole_set: pd.DataFrame, temp_data: pd.Series, i: int) -> None:

        self.counter += 1

        # print results to console if configuration in ini is 1
        if self.print_debug == 1:
            self.print_to_console(static_n, confidence_lvl, whole_set, temp_data, i)

        temp_dic_res = {
            OUTLIER_NO: str(self.counter),
            SUBSET_SIZE: str(static_n),
            SUBSET: str(temp_data.tolist()),
            NODE: str(whole_set[NODE].values[0]).replace("\t", ""),
            DATA_TYPE: whole_set[DATA_TYPE].values[0],
            INDEX_FIRST_ELEMENT: str(i),
            INDEX_LAST_ELEMENT: str(static_n + i - 1),

        }
        self.result.append(temp_dic_res)

    def get_appropriate_subset(self, static_n: int, whole_set: pd.DataFrame, confidence: dict) -> None:
        test_set = whole_set[VALUES]

        # list comprehension with UDF optimized on pd.DataFrame
        # read it like: for i in range if condition is true then print
        [
            self.results_to_list(static_n, confidence[KEY], whole_set, test_set[i:i + static_n].sort_values(), i)
            for i in range(len(test_set)-static_n)
            if self.get_result(test_set[i:i+static_n],
                               self.find_comparator(test_set[i:i+static_n], confidence[VALUE])) is True
        ]

    def run(self, confidence_level: dict) -> None:
        static_n = copy(self.static_n)
        while static_n <= self.static_n_maximum:
            self.grouped_data.apply(lambda grp: self.get_appropriate_subset(static_n, grp, confidence_level))
            # increment size
            static_n += 1

        self.save_file.run(pd.DataFrame(self.result), confidence_level[KEY])
