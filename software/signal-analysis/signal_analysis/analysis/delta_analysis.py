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

import logging
from statistics import mean, median

import numpy as np
from numpy import absolute
import matplotlib.pyplot as plt
from scipy.signal import find_peaks


class DeltaAnalysis:
    """
    Delta analysis

    https://www.mpa.ethz.ch/static/sttt/node1.html

    Is especially interesting for clock-signal SPI
    since here we can see the transmission blocks of SPI
    in the clock signal (for double event durations)
    """

    log = logging.getLogger(__module__)

    def __init__(self, verbatim, plot_all_delta_plots_individually,
                 interval_list,
                 min_event_amount_start,
                 event_amount_increase,
                 time_resolution, title=None):

        self.delta_min_level = []
        self.delta_max_level = []
        self.delta_time_array = []
        self.__min_intervals = []

        interval_min_list, interval_max_list = \
            self.__generate_delta_lists(interval_list,
                                        min_event_amount_start,
                                        event_amount_increase)
        if verbatim:
            self.__plotting_delta_min(
                time_resolution,
                interval_min_list,
                min_event_amount_start,
                event_amount_increase)
            self.__plotting_delta_max(
                time_resolution,
                interval_max_list,
                event_amount_increase)
        if plot_all_delta_plots_individually:
            self.__plot_delta_analysis(title)

    def get_transmission_block_duration(self):
        # self.__plot_durations_outliers_list()
        if not self.__min_intervals:
            return None

        indices_of_duration_characteristics = \
            self.__indices_of_transmission_characteristics(
                self.__min_intervals)
        if len(indices_of_duration_characteristics) >= 2:
            # print(f"Indices of duration characteristics: {indices_of_duration_characteristics}")
            low_transmission_break_deviation = \
                self.__transmission_break_variation_is_low(
                    indices_of_duration_characteristics)
            low_transmission_duration_deviation = \
                self.__transmission_duration_variation_is_low(
                    indices_of_duration_characteristics)
            # print(f"Low transmission break deviation: {low_transmission_break_deviation}")
            # print(f"Low transmission duration deviation: {low_transmission_duration_deviation}")
            if low_transmission_break_deviation and low_transmission_duration_deviation:
                duration_between_breaks = \
                    mean(self.__duration_between_characteristics(
                        indices_of_duration_characteristics))
                return duration_between_breaks

            return None

        if len(indices_of_duration_characteristics) == 0:
            return None

        return None

    @staticmethod
    def __generate_delta_level_array(time_resolution,
                                     delta_array_items,
                                     incident_startlevel,
                                     event_amount_increase):
        delta_array = []
        incident_level = incident_startlevel

        for i, item in enumerate(delta_array_items):
            if i == 0:
                indices_at_level = \
                    int(item / time_resolution)
                incident_block = \
                    [incident_level] * indices_at_level
            elif i > 0:
                indices_at_level = int((item
                                        - delta_array_items[i - 1])
                                       / time_resolution)
                incident_block = [incident_level] \
                    * indices_at_level
            delta_array.extend(incident_block)
            incident_level += event_amount_increase
        return delta_array

    @staticmethod
    def __duration_for_events(interval_list, index, event_amount):
        duration = sum(
            interval_list[index: (index + event_amount)])
        return duration

    @staticmethod
    def __generate_delta_time_array(time_resolution, delta_data):
        # Extend the data arrays to the max-array-length
        delta_array_length = len(delta_data)
        delta_time_array = np.arange(0,
                                     delta_array_length * time_resolution,
                                     time_resolution)
        return delta_time_array

    @staticmethod
    def __get_durations_from_interval_list(interval_min_list):
        intervals = []
        for i in range(1, len(interval_min_list), 1):
            interval_duration = (
                interval_min_list[i]
                - interval_min_list[i-1])
            intervals.append(interval_duration)
        return intervals

    def __generate_delta_lists(self, interval_list, min_event_amount_start,
                               event_amount_increase):
        """
        Generates RTC list either for single event
        ([high to low] or [low to high])
        or double event ([low + high until going low again]
        or high + low until going high again]).
        Could be implemented in the function parameters
        eventually, but currently a RTC with a single event does
        not make any sense
        """
        interval_min_list = []
        interval_max_list = []
        interval_list = absolute(interval_list)
        # !!!!!!!!!!!!
        # Arrays shortened to for debugging the algorithm
        # !!!!!!!!!!!!
        max_event_amount_limit = 60  # was 50
        event_list_length_insufficient = \
            (len(interval_list) < max_event_amount_limit)
        if event_list_length_insufficient:
            max_event_amount_limit = len(interval_list)

        # List with event amounts to be investigated:
        event_amount_range = \
            range(min_event_amount_start,
                  max_event_amount_limit,
                  event_amount_increase)
        for event_amount in event_amount_range:
            list_of_durations = []
            max_allowed_index = (
                (
                    len(interval_list)
                    - event_amount)
                + 1)
            # In the following line: "event_amount" added, since
            # the algorithm has to skip from low-high to low-high
            # instead of low-high, high-low, low-high, high-low
            for index in range(0, max_allowed_index, event_amount_increase):
                duration = self.__duration_for_events(
                    interval_list,
                    index,
                    event_amount)
                list_of_durations.append(duration)
                del duration
            interval_min_list.append(
                min(list_of_durations))
            interval_max_list.append(
                max(list_of_durations))
            del list_of_durations
        # print(interval_min_list)
        min_intervals = \
            self.__get_durations_from_interval_list(interval_min_list)
        self.__min_intervals = min_intervals
        self.log.debug("Min intervals: %s", min_intervals)
        return interval_min_list, interval_max_list

    @staticmethod
    def __rebase_to_maximum(interval_list):
        # Flipping the plot upside down
        maximum = max(interval_list)
        minimum = min(interval_list)
        duration_sum = maximum + minimum
        return [duration_sum - interval for interval in interval_list]

    def __find_short_duration_outliers(self, interval_list):
        """
        use https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.argrelextrema.html
        Alternatively: Mix lists of finding peaks and valleys,
        which return indices each, and mix those (sort for rising indices)
        """
        this_interval_list = interval_list.copy()
        # print(f"Interval list: {this_interval_list}")
        # Both functions used to get the *short duration* outliers
        # First function is meant as inversion
        # (shortest durations create the
        # highest peak) for getting the minima
        # second function for rebasing to the zero
        this_interval_list = self.__rebase_to_maximum(this_interval_list)

        self.log.debug("Rebased interval list: %s", this_interval_list)
        peaks_indices_list = find_peaks(this_interval_list,
                                        prominence=min(
                                            this_interval_list) * 0.5,
                                        width=[1, 1]
                                        )
        peaks_indices_list = peaks_indices_list[0]
        self.log.debug("Peaks indices list, short durations outliers: %s",
                       peaks_indices_list)
        return peaks_indices_list

    def __find_long_duration_outliers(self, interval_list):
        this_interval_list = interval_list.copy()
        self.log.debug("Interval list: %s", this_interval_list)

        peaks_indices_list = find_peaks(this_interval_list,
                                        prominence=min(
                                            this_interval_list) * 0.5,
                                        width=[1, 2]
                                        )
        peaks_indices_list = peaks_indices_list[0]
        self.log.debug("Peaks indices list long durations outliers: %s",
                       peaks_indices_list)
        return peaks_indices_list

    def __indices_of_transmission_characteristics(self, interval_list):
        peaks_indices_list = []
        peaks_indices_list.extend(
            self.__find_short_duration_outliers(interval_list))
        peaks_indices_list.extend(
            self.__find_long_duration_outliers(interval_list))
        peaks_indices_list.sort()
        self.log.debug("Indices of transmission characteristics %s",
                       peaks_indices_list)
        return peaks_indices_list

    def __transmission_break_variation_is_low(self,
                                              indices_of_duration_characteristics):
        durations = []
        for i in indices_of_duration_characteristics:
            durations.append(self.__min_intervals[int(i)])
        stddev = np.std(durations)
        med = median(durations)
        # print(f"Array of break durations: {durations}")
        # print(f"Stddev breaks: {stddev}; median breaks: {med}")
        return stddev < med * 0.2

    def __duration_between_characteristics(self,
                                           indices_of_duration_characteristics):
        durations = []
        for i in range(1, len(indices_of_duration_characteristics)):
            low_limit = indices_of_duration_characteristics[i-1] + 1
            high_limit = indices_of_duration_characteristics[i]
            duration = (sum(
                self.__min_intervals[low_limit: high_limit]))
            durations.append(duration)
        return durations

    def __transmission_duration_variation_is_low(self,
                                                 indices_of_duration_characteristics):
        durations = \
            self.__duration_between_characteristics(
                indices_of_duration_characteristics)
        stddev = np.std(durations)
        med = median(durations)

        # print(f"Stddev transmission: {stddev}; median transmission: {med}")
        return stddev < med * 0.05

    def __plotting_delta_min(self,
                             time_resolution,
                             interval_min_list,
                             min_event_amount_start,
                             event_amount_increase):

        delta_min_level = self.__generate_delta_level_array(
            time_resolution,
            interval_min_list,
            min_event_amount_start,
            event_amount_increase)
        delta_plot = plt.subplot(4, 3, 7)
        plt.subplots_adjust(wspace=0.35, hspace=0.8)
        delta_plot.set_title("Delta analysis")
        delta_plot.set_xlabel("Interval duration / ns")
        delta_plot.set_ylabel("Infimum amount of events within interval")
        delta_time_array = self.__generate_delta_time_array(
            time_resolution,
            delta_min_level)
        delta_plot.plot(delta_time_array, delta_min_level,
                        label='Min-array')

    def __plotting_delta_max(self,
                             time_resolution,
                             interval_max_list,
                             event_amount_increase):

        # Identifying and removing initial offset
        first_duration = interval_max_list[0]
        interval_max_list = [interval - first_duration
                             for interval in interval_max_list[1:]]

        delta_max_level = self.__generate_delta_level_array(
            time_resolution,
            interval_max_list,
            0,
            event_amount_increase)
        delta_plot = plt.subplot(4, 3, 10)
        delta_plot.set_xlabel("Interval duration after offset of "
                              + str(round(first_duration / 1000000, 2)) + " ms / ns")
        delta_plot.set_ylabel("Supremum amount of events within interval")
        delta_time_array = self.__generate_delta_time_array(
            time_resolution,
            delta_max_level)
        delta_plot.plot(delta_time_array, delta_max_level,
                        label='Max-array')

    def __plot_delta_analysis(self, title):
        # Plotting the read data
        plt.figure()
        plt.title(title)
        plt.plot(self.delta_time_array,
                 self.delta_min_level,
                 label='Min-durations')
        plt.plot(self.delta_time_array,
                 self.delta_max_level,
                 label='Max-durations')
        plt.xlabel('Interval duration / ns')
        plt.ylabel('Minimum/maximum amount of events')
        plt.legend()
        plt.show(block=False)
