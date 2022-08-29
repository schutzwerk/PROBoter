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
from math import floor
from statistics import mean

import scipy
import numpy

from signal_analysis.model import MeasurementSignal, PatternProperties, \
    EventIntervalProperties


class PatternAnalysis:
    """
    Helper class which finds the duration of a repeating pattern. Is required
    for UART, since the reoccuring voltage states of start- and stop bits
    define this repeating pattern.
    """

    log = logging.getLogger(__name__)

    @classmethod
    def analyze(cls, signal: MeasurementSignal,
                interval_results: EventIntervalProperties) -> PatternProperties:
        """
        Searches for a repeating pattern of voltage states.
        Returns the pattern interval in symbols and and in nanoseconds.
        """
        if signal.voltage_standard_deviation <= 50:
            return PatternProperties()

        meas_res_ns = signal.time_resolution
        cls.log.debug("Measurement resolution in ns: %d", meas_res_ns)

        activity_list = interval_results.transmission_activity_list
        index_longest_activity = interval_results.longest_activity
        start_time = activity_list[index_longest_activity][0]
        stop_time = activity_list[index_longest_activity][1]

        start_index = int(start_time / meas_res_ns)
        stop_index = int(stop_time / meas_res_ns)

        autocorrelation = cls.__autocorrelate(signal.voltage_data,
                                              start_index, stop_index)

        pattern_interval_indices = cls.__pattern_interval_indices(
            autocorrelation)

        if pattern_interval_indices is None:
            return PatternProperties()

        pattern_interval_ns = pattern_interval_indices * signal.time_resolution
        pattern_duration_in_symbols = pattern_interval_ns \
            / interval_results.first_reoccuring_duration
        cls.log.debug("First reoccuring duration: %s",
                      interval_results.first_reoccuring_duration)
        pattern_duration_in_symbols = round(pattern_duration_in_symbols, 2)
        cls.log.debug("Pattern duration in symbols: %s",
                      pattern_duration_in_symbols)

        return PatternProperties(
            repeating_pattern_duration_symbols=pattern_duration_in_symbols,
            repeating_pattern_duration_ns=pattern_interval_ns)

    @classmethod
    def __pattern_interval_indices(cls, autocorrelation):
        sample = autocorrelation.copy()
        sample = cls.__slice_interesting_range(sample)

        corr_peaks = cls.__get_correlation_peaks(sample)
        if len(corr_peaks) <= 10:
            cls.log.debug("Insufficient correlation peaks")
            return None

        if len(corr_peaks) > 10:
            intervals = cls.__get_intervals(corr_peaks)
            interval_length = cls.__get_pattern_length(intervals)
        return interval_length

    @staticmethod
    def __normalise(levels):
        """
        Shift voltage levels that |U_min| = |U_max|
        """
        average = mean([max(levels), min(levels)])
        voltage_range = (max(levels) - min(levels))
        normalisation_factor = voltage_range / 2
        return [(lvl - average) / normalisation_factor for lvl in levels]

    @staticmethod
    def __get_upper_half(array):
        # Since autocorrelation is symmetrical,
        # only upper half is
        # interesting for analysis
        return array[int(floor(len(array)/2)):]

    @classmethod
    def __autocorrelate(cls, voltage_levels, start_index, stop_index):
        voltage_levels = voltage_levels[start_index:stop_index]
        voltage_levels = cls.__normalise(list(voltage_levels))
        autocorr_array = scipy.signal.correlate(voltage_levels,
                                                voltage_levels)
        autocorr_array = cls.__get_upper_half(autocorr_array)
        return autocorr_array

    @classmethod
    def __slice_interesting_range(cls, sample):
        """
        Since the autocorrelation function trails off
        with increasing shift: Use only the first 10%
        of the autocorrelation signal.

        Additionally: Since on index 0 the sample
        autocorrelates with itself: Remove this giant peak!
        """
        # Removing trailing 80 % and :
        # Removing the giant initial peak:
        # frac_len_upper = int(len(sample) * 0.15)
        frac_len_upper = int(len(sample) * 0.2)
        first_peak_samples = int(len(sample) * 0.05)  # Was 0.01
        # TODO: Has been modified from 1e-3 to 2e-3
        # to remove the first initial peak
        sample = sample[first_peak_samples:frac_len_upper]

        # Rebasing the samples by the average value,
        # so that we can identify the peaks by using the half
        # of the absolute value as identification limit
        average_of_slice = mean(sample)
        cls.log.debug("Average value of slice: %f", average_of_slice)
        return [smpl - average_of_slice for smpl in sample]

    @classmethod
    def __get_correlation_peaks(cls, sample):
        """
        Find indeces of peaks.
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html
        """
        # For AVM UART: Peaks are correctly identified if indices-distance
        # is 86 or 87 or time-distance is approx. 8.6µs
        if len(sample) == 0:
            return []

        height = (max(sample) * 0.5)
        # prominence = (max(sample) * 0.525)
        list_of_found_peaks = scipy.signal.find_peaks(
            sample,
            height        # Trial and
            # prominence=prominence
        )
        list_of_found_peaks = list_of_found_peaks[0]
        cls.log.debug("Autorrelation peaks list: %s", list_of_found_peaks)
        cls.log.debug("Height requirement for the pattern peaks: %f", height)
        return list_of_found_peaks

    @classmethod
    def __get_intervals(cls, corr_peaks):
        intervals = []
        for i in range(1, len(corr_peaks)-5):
            delta = corr_peaks[i] - corr_peaks[i-1]
            intervals.append(delta)
        cls.log.debug("Autorrelation intervals list: %s", intervals)
        return intervals

    @staticmethod
    def __get_pattern_length(intervals):
        """
        Calculate the standard deviation of the intervals.
        If that is sufficiently small, we can consider
        that the repetition rate is constant
        """
        if len(intervals) >= 40:
            intervals = intervals[:40]
        stddev = numpy.std(intervals)
        avg = mean(intervals)
        if stddev < 0.1 * avg:
            return int(avg)
        if stddev > 0.1 * avg:
            return None
        return None
