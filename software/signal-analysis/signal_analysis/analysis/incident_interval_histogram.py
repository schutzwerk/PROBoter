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

import scipy
import numpy as np
import matplotlib.pyplot as plt


# The with of the created figures in mm
FIGURE_WIDTH = 51 * 6/5
# The height of the created figures in mm
FIGURE_HEIGHT = FIGURE_WIDTH / 3 * 2
# The font size to use in the chart legends
LEGEND_FONT_SIZE = 5
# The font family to use
FONT_FAMILY = "sans-serif"
# The folder where the plots will be saved


class IncidentIntervalHistogram:
    """
    Incident interval histogram
    """

    log = logging.getLogger(__module__)

    def __init__(self, interval_array, time_resolution_ns, verbatim=False):

        self.indices_of_rising_peaks = []
        self.indices_of_falling_peaks = []

        # Outgoing information
        self.incidents_durat_range = []
        self.rising = []
        self.falling = []

        self.first_reoccuring_duration_ns = None
        self.amount_of_reoccuring_events = 0
        self.are_durations_int_multiple = False

        amount_events = len(interval_array)
        interval_array = interval_array.copy()
        incidents_durat_range, hist_rising, hist_falling = \
            self.__generate_histograms(interval_array,
                                       time_resolution_ns)
        rising_peaks_indices, falling_peaks_indices = \
            self.__generate_histogram_peaks_indices(
                hist_rising,
                hist_falling,
                amount_events)
        self.first_reoccuring_duration_ns = \
            self.__get_shortest_incident_peak_duration_ns(
                incidents_durat_range, rising_peaks_indices,
                falling_peaks_indices)
        self.__determine_amount_of_reocc_events(
            rising_peaks_indices,
            falling_peaks_indices)
        self.log.debug("Rising indices: %s, falling indices: %s",
                       rising_peaks_indices, falling_peaks_indices)

        self.__warn_for_insufficient_sampling_rate(
            self.first_reoccuring_duration_ns,
            time_resolution_ns)
        self.incidents_durat_range = incidents_durat_range
        self.rising = hist_rising
        self.falling = hist_falling

        self.indices_of_rising_peaks = rising_peaks_indices
        self.indices_of_falling_peaks = falling_peaks_indices
        if len(rising_peaks_indices) + len(falling_peaks_indices) > 0:
            self.are_durations_int_multiple = \
                self.__are_duration_int_multiple(incidents_durat_range,
                                                 rising_peaks_indices,
                                                 falling_peaks_indices)
        if verbatim:
            self.__plot_histogram(incidents_durat_range, hist_rising,
                                  hist_falling)

    @property
    def event_peak_symmetry(self):
        rising_indices = self.indices_of_rising_peaks
        falling_indices = self.indices_of_falling_peaks
        self.log.debug("Rising indices: %s", rising_indices)
        self.log.debug("Falling indices: %s", falling_indices)
        are_same_indices = False
        for i in range(min(len(rising_indices), len(falling_indices))):
            for j in range(-2, +2):
                if rising_indices[i] == falling_indices[i]+j:
                    are_same_indices = True
        self.log.debug("I see symmetry, event_peak_symmetry-function: %s",
                       are_same_indices)
        return are_same_indices

    @classmethod
    def __get_shortest_incident_peak_duration_ns(cls, interval_range,
                                                 indices_of_rising_peaks,
                                                 indices_of_falling_peaks):
        # Identify available number of peaks
        no_peaks = (
            (len(indices_of_rising_peaks) == 0)
            and
            (len(indices_of_falling_peaks) == 0))
        single_peak_side = (
            (len(indices_of_rising_peaks) == 0)
            or
            (len(indices_of_falling_peaks) == 0))
        both_peak_sides = (
            (len(indices_of_rising_peaks) != 0)
            and
            (len(indices_of_falling_peaks) != 0))
        # Evaluate amount of available peaks
        if no_peaks:
            return 0

        peak_duration = None
        if single_peak_side:
            if len(indices_of_rising_peaks) == 0:
                peak_duration = int(
                    interval_range[indices_of_falling_peaks[0]])
            elif len(indices_of_falling_peaks) == 0:
                peak_duration = int(interval_range[indices_of_rising_peaks[0]])
            else:
                cls.log.info("There seems to be no change "
                             "on this line. No Symbol returned")

        if peak_duration is None and both_peak_sides:
            first_rising = indices_of_rising_peaks[0]
            first_falling = indices_of_falling_peaks[0]
            if first_rising < first_falling:
                peak_duration = int(interval_range[first_rising])
            elif first_rising > first_falling:
                peak_duration = int(interval_range[first_falling])
            elif first_rising == first_falling:
                peak_duration = int(interval_range[first_rising])
            else:
                cls.log.info("Symbol length could not be identified: "
                             "Missing element")
        return peak_duration

    @classmethod
    def __warn_for_insufficient_sampling_rate(cls, symbol_duration,
                                              time_resolution_ns):
        if symbol_duration < 20 * time_resolution_ns:
            cls.log.info("-------------------------------------------")
            cls.log.info("WARNING: Measurement sampling rate too long.")
            cls.log.info("Identification accuracy might suffer.")
            cls.log.info("Decrase sampling rate to a shorter interval.")
            cls.log.info("-------------------------------------------")

    @staticmethod
    def __extend_by_min_value(histogram):
        """
        scipy.signal.find_peaks function is rubbish when
        the maximum is at the first or last index.
        Therefore: Extend the list by the minimum value
        as first and as last element
        """
        histogram = histogram.tolist()
        min_value = min(histogram)
        histogram.insert(0, min_value)
        histogram.insert(len(histogram),
                         min_value)
        return histogram

    @staticmethod
    def __shift_peak_index_list(peak_list):
        """
        Since the find width-algorithm does not
        consider any peaks on the first index,
        we had add a minimum value at the lowest
        and highest index. Here, also the
        indeces for the found peaks need to be
        adapter, either.
        """
        return [peak - 1 for peak in peak_list]

    def __generate_indices_of_histogram_peaks(self, histogram,
                                              len_interval_array):
        # Generates list with indexes of
        # incident peaks from histogram
        '''
        Central function based on
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
        '''
        histogram = histogram.copy()
        histogram = \
            self.__extend_by_min_value(histogram)
        height = 0.05 * len_interval_array  # was 0.05
        # print(f"Event histogram peak minimum limit: {height}")
        # print(f"Height: {height}")
        distance = len(histogram) * 0.03  # was 0.25
        indices_of_peaks = \
            scipy.signal.find_peaks(
                histogram,
                height=height,
                distance=distance
            )
        indices_of_peaks = indices_of_peaks[0]
        return self.__shift_peak_index_list(indices_of_peaks)

    def __generate_histogram_peaks_indices(self, histogram_of_rising,
                                           histogram_of_falling, len_interval_array):
        indices_of_rising_peaks =\
            self.__generate_indices_of_histogram_peaks(
                histogram_of_rising, len_interval_array)
        indices_of_falling_peaks =\
            self.__generate_indices_of_histogram_peaks(
                np.abs(histogram_of_falling),
                len_interval_array)
        return indices_of_rising_peaks, indices_of_falling_peaks

    def __determine_amount_of_reocc_events(self, indices_of_rising_peaks,
                                           indices_of_falling_peaks):
        """
        Returns the amount of reoccuring durations
        == the number of peaks in the event incident
        histogram
        """
        amount_rising = len(indices_of_rising_peaks)
        amount_falling = len(indices_of_falling_peaks)
        sum_reoccuring_events = (amount_rising + amount_falling)
        self.amount_of_reoccuring_events = sum_reoccuring_events

    @staticmethod
    def __plot_histogram(incidents_durat_range, rising, falling):
        incident_histogram_plot = plt.subplot(235)
        incident_histogram_plot.set_title("Incident histogram")
        # plt.figure()
        # plt.title('Events in data array')
        incident_histogram_plot.set_ylabel("Amount of events")
        incident_histogram_plot.set_xlabel("Voltage state duration / us")
        incident_histogram_plot.plot((incidents_durat_range/1000), rising)
        incident_histogram_plot.plot((incidents_durat_range/1000), falling)
        # plt.xlabel("Range / ns")
        # plt.ylabel("Amount of events")
        # plt.show(block = False)

    @staticmethod
    def __generate_array_of_rising_incidents(interval_array):
        # Append minimum and maximum duration
        # to arrays of rising and falling
        # incidents first, to have the correct
        # length for the histogram
        rising_incidents_array = []
        rising_incidents_array.append(
            min(np.abs(interval_array)))
        rising_incidents_array.append(
            max(np.abs(interval_array)))
        # Adding the incident durations of rising
        # and falling incidents to the
        # respective arrays
        for interval in interval_array:
            if interval > 0:
                rising_incidents_array.append(interval)
        # for incident in rising_incidents_array:
        #     print(f'Rising incident duration: {incident}')
        return rising_incidents_array

    @staticmethod
    def __generate_array_of_falling_incidents(interval_array):
        # Append minimum and maximum duration
        # to arrays of rising and falling
        # incidents first, to have the correct
        # length for the histogram
        falling_incidents_array = []
        falling_incidents_array.append(
            min(np.abs(interval_array)))
        falling_incidents_array.append(
            max(np.abs(interval_array)))
        for interval in interval_array:
            if interval < 0:
                falling_incidents_array.append(interval * (-1))
        # for incident in falling_incidents_array:
        #     print(f'Falling incident duration: {incident}')
        return falling_incidents_array

    def __generate_interval_array_range(self, interval_array, amount_of_bins):
        # Generate incident interval array range
        binsize = (math.ceil
                   (
                       max(np.abs(interval_array))
                       - min(np.abs(interval_array))
                   )
                   / amount_of_bins)
        self.log.debug("min: %f, max:%f, binsize: %s",
                       min(np.abs(interval_array)),
                       max(np.abs(interval_array)),
                       binsize)
        incidents_durat_range = \
            np.arange(
                min(np.abs(interval_array)),
                max(np.abs(interval_array)),
                binsize)
        self.log.debug('Min-value in interval array: %s',
                       incidents_durat_range[0])
        self.log.debug('Max-value in interval array: %s',
                       incidents_durat_range[-1])
        return incidents_durat_range

    @staticmethod
    def __correct(histogram):
        # remove 1 from the smallest and
        # highest incidents, which we originally
        # added and only needed for the
        # correct scaling of the histogram
        histogram[0] = histogram[0] - 1
        histogram[-1] = histogram[-1] - 1
        return histogram

    @staticmethod
    def __flip_falling_incidents(falling_incidents):
        # Multiply the histogram values
        # of the falling incidents with
        # -1, so that I can plot and identify
        # the falling and rising incidents
        # in one plot
        for incident in falling_incidents:
            incident = (-1) * incident
        return falling_incidents

    @staticmethod
    def __remove_max_outliers(interval_array):
        """
        Had to remove the outliers from the maximum duration,
        like when nothing happens on the line.
        Had to implement, since otherwise this
        causes problems with the resolution.
        """
        interval_array.sort()
        # print(f"Intervall array: {interval_array}")
        # for data in interval_array:
        #     print(f'Data in interval array, pre-deletion: {data}')
        # print()
        removal_amount = int(math.ceil(len(interval_array) * 0.001))
        # print(f"Removal amount: {removal_amount}")
        # print(f"First 50 entries before filtering {interval_array[0:50]}")
        # print(f"Last 50 entries before filtering {interval_array[-50:]}")
        interval_array = interval_array[(
            2) * removal_amount:(-2)*removal_amount]
        # print(f"First 50 entries AFTER filtering {interval_array[0:50]}")
        # print(f"Last 50 entries AFTER filtering {interval_array[-50:]}")
        # print("")
        # input()
        # for data in interval_array:
        #     print(f'Data in interval array, post deletion: {data}')
        # print()
        return interval_array

    def __generate_rising_histogram(self, rescaled_interval_array,
                                    amount_of_bins):
        rising_incidents_array = \
            self.__generate_array_of_rising_incidents(
                rescaled_interval_array)
        histogram_rising, _ = \
            np.histogram(rising_incidents_array,
                         amount_of_bins)
        histogram_rising =\
            self.__correct(histogram_rising)
        return histogram_rising

    def __generate_falling_histogram(self, rescaled_interval_array,
                                     amount_of_bins):
        falling_incidents_array = \
            self.__generate_array_of_falling_incidents(
                rescaled_interval_array)
        histogram_falling, _ = \
            np.histogram(falling_incidents_array,
                         amount_of_bins)
        histogram_falling =\
            self.__correct(histogram_falling)
        histogram_falling =\
            self.__flip_falling_incidents(
                histogram_falling)
        return histogram_falling

    @classmethod
    def __rescale_to_resoltution(cls, filtered_interval_array,
                                 time_resolution_ns, amount_of_bins):
        # In case the most prominent events do have such similar
        # durations that the produced/displayed resolution would be
        # higher than the actually measured one:
        # Extend the list of intervals by an value sufficiently large
        # that the shown resolution fits to the actually measured one.

        # Time range between longest and shortest events
        event_duration_range = \
            max(np.abs(filtered_interval_array)) \
            - min(np.abs(filtered_interval_array))
        cls.log.debug("Minimum duration: %s", min(
            np.abs(filtered_interval_array)))
        cls.log.debug("Maximum duration: %s",
                      max(np.abs(filtered_interval_array)))
        cls.log.debug("Resolution in ns: %d", time_resolution_ns)

        # Actually required range, based on the time resolution and the amount
        # of bins
        resolution_based_range = time_resolution_ns * amount_of_bins
        if event_duration_range < resolution_based_range:
            # START of faulty CODE
            # if(False):
            # print("Walking into artificial resolution range")

            delta_range = resolution_based_range - event_duration_range
            # print(f"Delta range: {delta_range}")
            artificial_duration = \
                delta_range + min(np.abs(filtered_interval_array))
            # print(f"Artificial duration: {artificial_duration}")
            filtered_interval_array.append(artificial_duration)
            filtered_interval_array.append(artificial_duration * -1)

            # print("!!!!IncidentIntervalHistogram.py contains bad code in\
            # lines 477 to 484: The artificial length extension might be\
            # bullshit! Redo!!")
            # END OF FAULTY CODE
        return filtered_interval_array

    def __generate_histograms(self, interval_array, time_resolution_ns):
        filtered_interval_array = self.__remove_max_outliers(interval_array)
        amount_of_bins = 100  # TODO change back to 100
        rescaled_interval_array = self.__rescale_to_resoltution(filtered_interval_array,
                                                                time_resolution_ns, amount_of_bins)
        incidents_durat_range = self.__generate_interval_array_range(
            rescaled_interval_array,
            amount_of_bins)

        # According to https://numpy.org/doc/stable/reference/generated/numpy.arange.html,
        # the function has the tendency to produce too many elements due to an
        # rounding error. Therefore, remove the superfluous element.
        if len(incidents_durat_range) != amount_of_bins:
            incidents_durat_range = incidents_durat_range[:-1]
        histogram_rising = self.__generate_rising_histogram(
            rescaled_interval_array,
            amount_of_bins)
        histogram_falling = self.__generate_falling_histogram(
            rescaled_interval_array,
            amount_of_bins)

        # Removing rescaling additive from histograms, if present
        # Otherwise it only removes one event counter from each histogram
        histogram_rising[-1] = histogram_rising[-1] - 1
        histogram_falling[-1] = histogram_falling[-1] - 1

        return incidents_durat_range, histogram_rising, histogram_falling

    @classmethod
    def __are_duration_int_multiple(cls, incidents_duration_range,
                                    rising_peaks_indices, falling_peaks_indices):
        cls.log.debug("Rising peaks indices: %s", rising_peaks_indices)
        cls.log.debug("Falling peaks indices: %s", falling_peaks_indices)
        all_peaks = rising_peaks_indices + falling_peaks_indices
        all_peaks.sort()
        # Following line removes duplicates
        all_peaks = list(dict.fromkeys(all_peaks))
        list_of_event_durations = []
        for i in all_peaks:
            list_of_event_durations.append(incidents_duration_range[i])
        cls.log.debug("All durations: %s", list_of_event_durations)
        first_duration = list_of_event_durations[0]
        range_limit = 0.2
        are_integer_multiple = all(
            (
                (((duration / first_duration) + range_limit) % 1)
                < (2 * range_limit))
            for duration in list_of_event_durations)
        del list_of_event_durations
        cls.log.debug("Are durations multiple: %s", are_integer_multiple)
        return are_integer_multiple
