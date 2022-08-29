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
from copy import copy
from typing import Optional

import scipy
import numpy as np
from numpy import absolute
import matplotlib.pyplot as plt

from signal_analysis.model import MeasurementSignal, EventIntervalProperties, \
    SignalType

from .delta_analysis import DeltaAnalysis
from .incident_interval_histogram import IncidentIntervalHistogram


class EventIntervalAnalysis:
    """
    Event interval analysis
    """

    log = logging.getLogger(__module__)

    def __init__(self, signal: MeasurementSignal,
                 plot_all_delta_plots_individually=False, verbatim=False):

        self.__signal = signal
        self.__voltage_levels = copy(self.__signal.voltage_data)
        self.__time_resolution_ns = self.__signal.time_resolution

        # Processing information
        self.__single_interval_array = []  # Incident interval array
        # Objects for generating information
        self.__delta_analysis = None

        # Outgoing information
        self.array_of_incidents = []
        self.first_reoccuring_duration_ns = None
        self.first_reoccuring_event_pair_duration_ns = None
        self.event_duration_symmetry = False
        self.amount_of_reoccuring_events = 0
        self.amount_of_reocc_event_pairs = 0
        self.are_state_durations_int_multiple = False

        denoised_voltage_levels = self.__apply_noise_filter(
            self.__voltage_levels)
        single_interval_array = self.__generate_interval_array(
            denoised_voltage_levels,
            self.__time_resolution_ns)

        if len(single_interval_array) > 4:
            double_interval_array =\
                self.__generate_double_interval_array(
                    single_interval_array)
            self.__perform_event_histograms_evaluation(verbatim,
                                                       single_interval_array,
                                                       double_interval_array,
                                                       self.__time_resolution_ns)

            self.__perform_delta_plot_evaluation(verbatim,
                                                 plot_all_delta_plots_individually,
                                                 single_interval_array,
                                                 self.__time_resolution_ns)

        self.__single_interval_array = single_interval_array

    @property
    def amount_of_found_events(self) -> int:
        """
        Return the number of determined events
        """
        return len(self.__single_interval_array)

    @property
    def longest_activity(self) -> int:
        index_of_max = 0
        max_duration = 0
        activity_list = self.tramsmission_activity_list
        for i, activity in enumerate(activity_list):
            start_time = activity[0]
            stop_time = activity[1]
            duration = stop_time - start_time
            if duration > max_duration:
                max_duration = duration
                index_of_max = i
        return index_of_max

    @property
    def voltage_of_longest_duration(self) -> float:
        single_interval_array = self.__single_interval_array.copy()
        interval = self.__find_middle_of_extremum(
            single_interval_array)
        index = int(interval / self.__time_resolution_ns)
        return int(self.__voltage_levels[index])

    @property
    def transmission_block_duration(self) -> Optional[int]:
        if self.__delta_analysis is not None:
            delta = self.__delta_analysis
            duration = delta.get_transmission_block_duration()
        else:
            duration = None
        return duration

    @property
    def event_interval_array(self):
        return np.abs(self.__single_interval_array.copy())

    @property
    def signed_event_interval_array(self):
        return self.__single_interval_array.copy()

    @property
    def signal_type(self) -> SignalType:
        """
        Currently based on voltage as well as incident evaluation.
        Can also be implemented in incident evaluation only:
        Dead/Power line signals have a continuous and no discrete
        event histogram spectrum.
        """
        voltage_mean = self.__signal.voltage_mean
        voltage_stddev = self.__signal.voltage_standard_deviation
        self.log.debug("Of signal %s the mean is %f and stddev is %f",
                       self.__signal.source_name, voltage_mean, voltage_stddev)

        amount_reoccuring_durations = self.amount_of_reoccuring_events
        amount_of_events = self.amount_of_found_events

        signal_type = SignalType.UNKNOWN
        if voltage_stddev <= 50:
            if voltage_stddev > voltage_mean:
                signal_type = SignalType.GROUND
            elif voltage_stddev < voltage_mean:
                signal_type = SignalType.CONST_VOLTAGE
        elif voltage_stddev > 50:
            if amount_reoccuring_durations == 2:
                if amount_of_events < 10:
                    signal_type = SignalType.SPORADIC
                elif amount_of_events >= 10:
                    signal_type = SignalType.PERIODIC
            elif amount_reoccuring_durations > 2:
                if amount_of_events < 10:
                    signal_type = SignalType.SPORADIC
                elif amount_of_events >= 10:
                    signal_type = SignalType.BURST
            elif amount_reoccuring_durations < 2:
                signal_type = SignalType.UNKNOWN

        return signal_type

    @property
    def time_first_activity(self) -> float:
        return abs(self.__single_interval_array[0])

    @property
    def time_last_activity(self) -> float:
        single_interval_array = self.__single_interval_array.copy()
        single_interval_array = absolute(single_interval_array)
        # print(f"Interval array: {single_interval_array}")
        total_duration = sum(single_interval_array[:-1])
        return total_duration

    @property
    def timelist_of_incidents(self):
        timelist_of_incidents = []
        for i, incident in enumerate(self.array_of_incidents):
            if incident != 0:
                time = self.__time_resolution_ns * i
                timelist_of_incidents.append(time)
        return timelist_of_incidents

    @property
    def tramsmission_activity_list(self):
        activity_list = []
        symbol_duration = self.first_reoccuring_duration_ns
        interval_durations = absolute(self.__single_interval_array)
        start_index = 0
        stop_index = 0

        for i in range(len(interval_durations) - 1):
            # Find prolonged duration which marks stop
            # of transmission activity
            #
            # Break has originally been 10 symbols
            # Prolonged since data signal sometimes
            # have signals of such duration, which are
            # then misinterpreted as breaks.
            is_sufficiently_long_break = \
                (interval_durations[i] >= 200 *
                 symbol_duration)  # was 200 * symbol_duration
            if is_sufficiently_long_break:
                stop_index = i
                message_duration =\
                    sum(interval_durations[start_index:stop_index])
                is_sufficiently_long_transmission_activity = \
                    (message_duration >= 50 *
                     symbol_duration)  # was 50 * symbol_duration
                if is_sufficiently_long_transmission_activity:
                    transmission_entry = []
                    start_ns = sum(interval_durations[0:start_index])
                    stop_ns = start_ns + message_duration
                    self.log.debug(("Start of activiy interval %.2e 	"
                                    "until stop of activity interval %.2e"),
                                   start_ns, stop_ns)
                    transmission_entry.append(start_ns)
                    transmission_entry.append(stop_ns)
                    activity_list.append(transmission_entry)
                    start_index = stop_index + 1
                else:
                    start_index = stop_index + 1
                    stop_index = stop_index + 1

        start_ns = sum(interval_durations[0:start_index])
        stop_ns = sum(interval_durations[:-1])
        transmission_entry = []
        transmission_entry.append(start_ns)
        transmission_entry.append(stop_ns)
        activity_list.append(transmission_entry)

        return activity_list

    @property
    def event_properties(self) -> EventIntervalProperties:
        result = EventIntervalProperties()
        result.interval_array = self.event_interval_array
        result.signed_interval_array = self.signed_event_interval_array
        result.transmission_activity_list = self.tramsmission_activity_list
        result.amount_reoccuring_durations = self.amount_of_reoccuring_events
        result.amount_of_events = self.amount_of_found_events
        result.amount_of_event_pairs = self.amount_of_reocc_event_pairs
        result.longest_activity = self.longest_activity
        result.event_duration_symmetry = self.event_duration_symmetry
        result.first_reoccuring_duration = self.first_reoccuring_duration_ns
        result.double_event_duration = self.first_reoccuring_event_pair_duration_ns
        result.time_first_activity = self.time_first_activity
        result.time_last_activity = self.time_last_activity
        result.transmission_block_duration = self.transmission_block_duration
        result.timelist_of_incidents = self.timelist_of_incidents
        result.voltage_of_longest_duration = self.voltage_of_longest_duration
        result.are_state_durations_int_multiple = self.are_state_durations_int_multiple
        result.signal_type = self.signal_type

        return result

    @staticmethod
    def __schmitt_trigger_high(data):
        # Schmitt trigger high threshold
        min_val = min(data)
        max_val = max(data)
        trigger = 0.7 * (max_val - min_val)
        return min_val + trigger

    @staticmethod
    def __schmitt_trigger_low(data):
        # Schmitt trigger min threshold
        min_val = min(data)
        max_val = max(data)
        trigger = 0.3 * (max_val - min_val)
        return min_val + trigger

    def __generate_array_of_incidents(self, data):
        array_of_incidents = [0] * len(data)

        # Define Schmitt trigger levels;
        # has been 0.7 and 0.3 as written in
        # SPI-spec
        # For finding the confirmation peaks
        # for SPI, we changed the trigger
        # levels to 0.5 and 0.2 respectively...
        # which leads to asymmetrical
        # trigger durations, which, again,
        # leads to false measurement data
        trigger_low = self.__schmitt_trigger_low(data)
        trigger_high = self.__schmitt_trigger_high(data)

        # initialise current state
        above_trigger = data[0] > trigger_high
        below_trigger = data[0] < trigger_low
        if not above_trigger:
            current_state = 0
        elif not below_trigger:
            current_state = 1

        # Marking events
        for i, entry in enumerate(data):
            above_trigger = entry > trigger_high
            below_trigger = entry < trigger_low
            if above_trigger and (current_state == 0):
                array_of_incidents[i] = 1
                current_state = 1
            elif below_trigger and (current_state == 1):
                array_of_incidents[i] = -1
                current_state = 0

        # Add event at the end of the list
        # to mark prolonged time
        # without any changes of signal
        if current_state == 0:
            array_of_incidents[-1] = 1
        elif current_state == 1:
            array_of_incidents[-1] = -1
        self.array_of_incidents = array_of_incidents
        return array_of_incidents

    @staticmethod
    def __generate_time_array(denoised_voltage_levels, time_resolution_ns):
        array_len = len(denoised_voltage_levels)
        max_time = time_resolution_ns * array_len
        time_array = range(0,
                           max_time,
                           time_resolution_ns)
        return time_array

    @staticmethod
    def __apply_noise_filter(voltage_levels):
        # Bessel filter:
        # https://docs.scipy.org/doc/scipy-0.14.0/reference/generated/scipy.signal.bessel.html
        # b, a = signal.bessel(4, 100, 'low', analog=True)

        # Raised cosine-filter
        # https://commpy.readthedocs.io/en/latest/generated/commpy.filters.rrcosfilter.html
        # sampling_frequency = 1/(self.__time_resolution_ns) * 1e9
        # time_idx, filtered_signal = rrcosfilter(len(self.__voltage_levels), 0.5, 1e-6,
        #         sampling_frequency)

        # https://docs.scipy.org/doc/scipy/
        # reference/generated/
        # scipy.ndimage.gaussian_filter.html
        #
        # sigma (standard deviation) is set to 3
        # which results in a rather
        # tight filter (avoids the curvatures
        # at edges), but for signal with an insufficient
        # time resolution, the edges will be flattened to just
        # one upper or lower level
        filtered_signal =\
            scipy.ndimage.gaussian_filter(
                voltage_levels, 1)
        return filtered_signal

    def __generate_interval_array(self, denoised_voltage_levels,
                                  time_resolution_ns):
        # Generates incident interval array
        array_of_incidents =\
            self.__generate_array_of_incidents(
                denoised_voltage_levels)
        time_array = self.__generate_time_array(
            denoised_voltage_levels,
            time_resolution_ns)
        incident_interval_array = []
        index_of_last_incident = 0
        # Filling incident array:
        for i, incident in enumerate(array_of_incidents):
            if incident == 1:
                incident_interval_array.append(
                    float(time_array[i]
                          - time_array[index_of_last_incident]))
                index_of_last_incident = i
            elif incident == -1:
                incident_interval_array.append(
                    float(time_array[i]
                          - time_array[index_of_last_incident])
                    * (-1))
                index_of_last_incident = i

        return incident_interval_array

    def __generate_double_interval_array(self, incident_interval_array):
        # Generates double incident
        # interval array
        incident_interval_array = absolute(
            incident_interval_array)
        # print(f"Start of Incident interval array {incident_interval_array[:100]}")
        double_incident_interval_array = []
        # Find way that the double event duration starts with the
        # beginning of a new signal transmission instead
        # of a fixed number "2"? This way, there currently is a
        # 50% chance to select the wrong start...
        # ... but at least the starting offset of 2 leads to the
        # correct evaluation for at least one OneWire protocol.
        for i in range(2, len(incident_interval_array), 2):
            double_incident_interval_array.append(
                incident_interval_array[i] +
                incident_interval_array[i-1])
        self.log.debug("Start of double incident interval array %s",
                       double_incident_interval_array[:100])
        return double_incident_interval_array

    def __find_index_of_maximum(self,
                                single_interval_array):
        maximum = max(self.__single_interval_array)
        index = single_interval_array.index(maximum)
        return index

    def __find_index_of_minimum(self,
                                single_interval_array):
        minimum = min(self.__single_interval_array)
        index = single_interval_array.index(minimum)
        return index

    def __find_middle_of_extremum(self, single_interval_array):
        max_interval_duration_is_high_state = (
            max(absolute(single_interval_array)) ==
            max(single_interval_array))
        max_interval_duration_is_low_state = (
            max(absolute(single_interval_array)) ==
            min(single_interval_array) * -1)
        if max_interval_duration_is_high_state:
            index_of_max_dur = self.__find_index_of_maximum(
                single_interval_array)
            duration_till_maximum =\
                sum(absolute(
                    single_interval_array[:index_of_max_dur]))
            duration_till_middle_of_extremum =\
                duration_till_maximum\
                + (max(single_interval_array)/2)
        elif max_interval_duration_is_low_state:
            index_of_max_dur = self.__find_index_of_minimum(
                single_interval_array)
            duration_till_minimum =\
                sum(absolute(
                    single_interval_array[:index_of_max_dur]))
            duration_till_middle_of_extremum =\
                duration_till_minimum\
                - (min(single_interval_array)/2)
        return duration_till_middle_of_extremum

    def __perform_event_histograms_evaluation(self, verbatim,
                                              single_interval_array, double_interval_array,
                                              time_resolution_ns):
        # Investigation of incident_histograms
        abs_sing_int_array = absolute(single_interval_array)

        if max(abs_sing_int_array) != min(abs_sing_int_array):
            single_inc_hist = IncidentIntervalHistogram(
                single_interval_array, time_resolution_ns,
                verbatim)
            self.first_reoccuring_duration_ns = \
                single_inc_hist.first_reoccuring_duration_ns
            self.event_duration_symmetry = \
                single_inc_hist.event_peak_symmetry
            self.amount_of_reoccuring_events =\
                single_inc_hist.amount_of_reoccuring_events
            self.are_state_durations_int_multiple =\
                single_inc_hist.are_durations_int_multiple

        abs_doub_int_array = absolute(double_interval_array)
        if max(abs_doub_int_array) != min(abs_doub_int_array):
            double_incident_histogram =\
                IncidentIntervalHistogram(double_interval_array,
                                          time_resolution_ns)
            self.first_reoccuring_event_pair_duration_ns = \
                double_incident_histogram.first_reoccuring_duration_ns
            self.amount_of_reocc_event_pairs = \
                double_incident_histogram.amount_of_reoccuring_events

    def __perform_delta_plot_evaluation(self, verbatim,
                                        plot_all_delta_plots_individually,
                                        single_interval_array,
                                        time_resolution_ns):
        # Investigation of RTCs
        min_event_amount_start = 2
        event_amount_increase = 2
        unmodified_interval_array = single_interval_array.copy()
        shifted_interval_array = unmodified_interval_array[1:]

        if not plot_all_delta_plots_individually:
            self.__delta_analysis = \
                DeltaAnalysis(verbatim,
                              plot_all_delta_plots_individually,
                              shifted_interval_array,
                              min_event_amount_start,
                              event_amount_increase,
                              time_resolution_ns)

        if plot_all_delta_plots_individually:
            # Double event durations, starting with  first event
            self.__delta_analysis = \
                DeltaAnalysis(verbatim, plot_all_delta_plots_individually,
                              unmodified_interval_array,
                              min_event_amount_start,
                              event_amount_increase,
                              self.__time_resolution_ns,
                              title="Double event duration, starting with first event")

            # Double event durations, starting with second event
            self.__delta_analysis = \
                DeltaAnalysis(verbatim, plot_all_delta_plots_individually,
                              shifted_interval_array,
                              min_event_amount_start,
                              event_amount_increase,
                              self.__time_resolution_ns,
                              title="Double event duration, starting with second event")
            # Single event duration, starting with first event
            min_event_amount_start = 2
            event_amount_increase = 1
            self.__delta_analysis = \
                DeltaAnalysis(verbatim, plot_all_delta_plots_individually,
                              unmodified_interval_array,
                              min_event_amount_start,
                              event_amount_increase,
                              self.__time_resolution_ns,
                              title="Single event duration, starting with first event")
            every_second_event = unmodified_interval_array[::2]
            self.__delta_analysis = \
                DeltaAnalysis(verbatim, plot_all_delta_plots_individually,
                              every_second_event,
                              min_event_amount_start,
                              event_amount_increase,
                              self.__time_resolution_ns,
                              title="Only high signal level events")

            every_second_event_starting_on_2 = shifted_interval_array[::2]
            self.__delta_analysis = \
                DeltaAnalysis(verbatim, plot_all_delta_plots_individually,
                              every_second_event_starting_on_2,
                              min_event_amount_start,
                              event_amount_increase,
                              self.__time_resolution_ns,
                              title="Only low signal level events")
            plt.show(block=True)
