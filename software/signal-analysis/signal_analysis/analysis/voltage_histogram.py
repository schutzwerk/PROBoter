# Copyright (C) 2022  SCHUTZWERK GmbH
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import math
import logging
from typing import Iterable, List

import numpy as np
import scipy.signal

from signal_analysis.model import VoltageLevelProperties


class VoltageHistogram:
    """
    Voltage level histogram
    """

    log = logging.getLogger(__module__)

    def __init__(self, voltage_levels: List[float]):
        self.__list_of_found_peaks = []
        self.__peak_widths = []
        self.__voltage_histogram_occurances = []
        self.__voltage_histogram_voltages_list = []

        # Analyze the data
        self.__generate_voltage_histogram(voltage_levels)
        self.__generate_list_of_voltage_peaks()
        self.__evaluate_peak_widths()
        self.log.debug('Amount of voltage levels: %d',
                       self.number_voltage_levels)

    @property
    def number_voltage_levels(self) -> int:
        """
        Return the number of distinct voltage levels
        """
        return len(self.__list_of_found_peaks)

    @property
    def main_voltage_levels(self) -> Iterable[float]:
        """
        Return a collection containing all distinct voltage levels
        """
        main_voltages_list = []
        for peak in self.__list_of_found_peaks:
            voltage = self.__voltage_histogram_voltages_list[peak]
            main_voltages_list.append(voltage)
        self.log.debug("Main voltage levels: %s", main_voltages_list)
        return main_voltages_list

    @property
    def rel_width_of_lowest_level(self) -> int:
        """
        Get relative width of lowest voltage level
        """
        lower_width = self.__peak_widths[0]
        total_voltage_range = len(self.__voltage_histogram_voltages_list)
        relative_width = lower_width / total_voltage_range * 100
        return int(relative_width)

    @property
    def rel_width_of_uppest_level(self) -> int:
        """
        Get relative width of highest voltage level
        """
        upper_width = self.__peak_widths[-1]
        total_voltage_range = len(self.__voltage_histogram_voltages_list)
        relative_width = upper_width / total_voltage_range * 100
        return int(relative_width)

    @property
    def voltage_level_properties(self) -> VoltageLevelProperties:
        """
        Return a bundled set of voltage level properties
        """
        result = VoltageLevelProperties()
        result.number_of_voltage_levels = self.number_voltage_levels
        result.relative_width_of_upper_voltage_level = self.rel_width_of_uppest_level
        result.relative_width_of_lowest_voltage_level = self.rel_width_of_lowest_level
        result.main_voltage_levels = self.main_voltage_levels
        return result

    def __generate_voltage_range(self, voltage_array: List[float],
                                 histogram_size: int) -> List[float]:
        binsize = round(
            (
                max(voltage_array)
                - min(voltage_array)
            )
            / histogram_size, 2)
        voltage_range = \
            np.arange(
                min(voltage_array),
                max(voltage_array),
                binsize)
        self.log.debug("Min-voltage: %f; max-voltage: %f",
                       min(voltage_array), max(voltage_array))
        self.log.debug("Voltage histogram-range: %s", voltage_range)
        return voltage_range

    def __generate_voltage_histogram(self, voltage_array: List[float]) -> None:
        """
        Generates two arrays:
          One for the voltage along the x-axis
          One with the number of occurances on the y-axis
        """

        # There still seems to be a bug in here:
        # The 0V measured are not at the 0V in the histogram
        # The following code under C seems to solve this the closest
        # http://courses.cs.vt.edu/~cs4234/F13/proj2/histogram.c
        #
        # Yet still, the code part of "int Which_bin" does not
        # seem to make much sense so far
        histogram_size = 50
        maximum_voltage = max(voltage_array)
        voltage_range = self.__generate_voltage_range(voltage_array,
                                                      histogram_size)

        if len(voltage_range) != histogram_size:
            # According to
            # https://numpy.org/doc/stable/reference/generated/numpy.arange.html,
            # the function has the tendency to produce too many elements
            # due to an rounding error. Therefore, remove the superfluous
            # element.
            voltage_range = voltage_range[:-1]

        voltage_histogram, _ = np.histogram(voltage_array,
                                            histogram_size)

        voltage_histogram = voltage_histogram.tolist()
        self.__voltage_histogram_occurances = voltage_histogram
        self.__voltage_histogram_voltages_list = voltage_range
        self.log.debug("Max voltage measured: %f", maximum_voltage)
        self.log.debug("Max voltage generated by histogram: %f",
                       max(self.__voltage_histogram_voltages_list))
        self.log.debug("Length of voltage histogram array: %d",
                       len(self.__voltage_histogram_voltages_list))

    @staticmethod
    def __extend_by_min_value(voltage_histogram: List[float]) -> List[float]:
        """
        scipy.signal.find_peaks function is rubbish when
        the maximum is at the first or last index.
        Therefore: Extend the list by the minimum value
        as first and as last element
        """
        min_value = min(voltage_histogram)
        voltage_histogram.insert(0, min_value)
        voltage_histogram.insert(len(voltage_histogram),
                                 min_value)
        return voltage_histogram

    def __generate_list_of_voltage_peaks(self) -> None:
        """
        Central function based on
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
        """
        voltage_histogram = \
            self.__voltage_histogram_occurances.copy()
        required_indices = len(voltage_histogram)
        voltage_histogram = \
            self.__extend_by_min_value(voltage_histogram)

        distance = int(required_indices*0.2)
        # For scaling the peak prominence correctly into logarithmic
        # scale: The next lower peak shall be at least 0.4 of the
        # height of the maximum peak prominence
        minvoltage = min(voltage_histogram)
        if minvoltage == 0:
            minvoltage = 1
        prominence = 10**(
            math.log10(max(voltage_histogram) / minvoltage) * 0.4
        ) * minvoltage
        # print(f"Voltage peak prominence {prominence}")
        list_of_found_peaks_scipy = \
            scipy.signal.find_peaks(
                voltage_histogram,
                distance=distance,
                prominence=prominence
            )
        list_of_found_peaks = list_of_found_peaks_scipy[0]
        # Since the voltage histogram had to be modified in the
        # __extend_by_min_value-function, this function corrects the the shift
        list_of_found_peaks = [peak - 1 for peak in list_of_found_peaks]
        self.__list_of_found_peaks = list_of_found_peaks

    def __evaluate_peak_widths(self) -> None:
        """
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.peak_widths.html
        """
        voltage_histogram = \
            self.__voltage_histogram_occurances.copy()
        voltage_histogram = \
            self.__extend_by_min_value(voltage_histogram)
        list_of_found_peaks = \
            self.__list_of_found_peaks.copy()

        # Since the find width-algorithm does not consider any peaks on the
        # first index, we had add a minimum value at the lowest and highest
        # index. Here, also the indeces for the found peaks need to be adapter,
        # either.
        list_of_found_peaks = [peak + 1 for peak in list_of_found_peaks] \

        widths, _, __, ___ =\
            scipy.signal.peak_widths(voltage_histogram,
                                     list_of_found_peaks, rel_height=0.999)
        self.__peak_widths = widths
