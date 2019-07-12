"""For some datatypes you could recieved as API response, here are filter according to your needs of filtering.
you just will need cast the data recieved to datatypes handled by your concrete filter."""


import abc
import numpy as np


class FilterType(abc.ABC):
    """Base class for filter objects"""
    @abc.abstractmethod
    def add_filter(self, filter_config):
        """For each trigger you add a filter for that trigger. with a propper filter config"""
        pass

    @abc.abstractmethod
    def add_empty_cell(self):
        """In case that a trigger hasnt a filtering need an empty filter will holded for that trigger. That "empty"
        filter can be anything, just must pass whatever compares as valid"""
        pass

    @abc.abstractmethod
    def seal_filter(self):
        """At configuration time, the filter configs are holded in a python list, when you seal a trigger that list
        is casted to a numpy array"""
        pass

    @abc.abstractmethod
    def filter(self, data_frame):
        """this method run the filters and return a boolean numpy array. if a cell is true means that triggers at true
         index must be called"""
        pass


@FilterType.register
class CuantityRange(FilterType):
    """filter for numbers. Can be a concrete number, a range, or a upper or lower limit"""
    def __init__(self):
        self._min_values = []
        self._max_values = []
        self._adding_alias = {'greater': self.add_min_value,
                              'less': self.add_max_value,
                              'between': self.add_range_value,
                              'equal': self.add_equal_value}

    def add_filter(self, filter_config):
        """add the filter config to certain trigger call. filter config must be a dictionary with "being" keyword
        and a value which can be "greater", "less", "between" and "equal". And anothes keyword named "values" which
        value is a number to compare (if the keyword is between, the value must be a list [min_value, max_value])"""
        self._adding_alias[filter_config['being']](filter_config['values'])

    """the next 4 methods are called throw add_filter"""

    def add_min_value(self, min_number):
        self._min_values.append(min_number)
        self._max_values.append(float('NaN'))

    def add_max_value(self, max_number):
        self._min_values.append(float('NaN'))
        self._max_values.append(max_number)

    def add_range_value(self, range_numbers):
        self._min_values.append(range_numbers[0])
        self._max_values.append(range_numbers[1])

    def add_equal_value(self, equal_number):
        self._min_values.append(equal_number)
        self._max_values.append(equal_number)

    def add_empty_cell(self):
        self._min_values.append(float('NaN'))
        self._max_values.append(float('NaN'))

    def seal_filter(self):
        self._min_values = np.array(self._min_values, dtype=np.float64)
        self._max_values = np.array(self._max_values, dtype=np.float64)

    def filter(self, data_frame):
        float_data = float(data_frame)
        return ((self._min_values <= float_data) + np.isnan(self._min_values)) * \
               ((self._max_values >= float_data) + np.isnan(self._max_values))


@FilterType.register
class BaseBoolString(FilterType, abc.ABC):
    """Base class to BoolString filter types. The idea here is treat integer as chained booleans Eg:
    21 = 10101 = [True, False, True, False, True]"""
    def __init__(self):
        self._bool_string_list = []

    def add_filter(self, filter_config):
        self._bool_string_list.append(filter_config)

    def add_empty_cell(self):
        self._bool_string_list = self._bool_string_list.append(int('0b' + '1' * 64, 2))

    def seal_filter(self):
        self._bool_string_list = np.array(self._bool_string_list, dtype=np.uint64)

    @abc.abstractmethod
    def filter(self, data_frame):
        pass


@BaseBoolString.register
class HardBoolString(BaseBoolString):
    """Sub class of BoolString where only is returned true if the dataframe has every asked boolean"""
    def __init__(self):
        super(HardBoolString, self).__init__()

    def filter(self, data_frame):
        int_to_filter = int(data_frame)
        return self._bool_string_list & int_to_filter == self._bool_string_list


@BaseBoolString.register
class SoftBoolString(BaseBoolString):
    """Sub class of BoolString where only is returned true if the dataframe has at least one asked boolean"""
    def __init__(self):
        super(SoftBoolString, self).__init__()

    def filter(self, data_frame):
        int_to_filter = int(data_frame)
        return self._bool_string_list & int_to_filter != 0
