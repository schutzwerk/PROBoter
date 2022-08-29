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
from typing import Iterable

from signal_analysis.model import SignalGroup, SignalType, AnalysedSignal


class SignalGroupAggregator:
    """
    Signal group aggregator
    """

    log = logging.getLogger(__name__)

    @classmethod
    def aggregate(cls, signal_results: Iterable[AnalysedSignal]) -> Iterable[SignalGroup]:
        """
        Aggregate given voltage signals to tuples of four signals that
        might belong to the same communication protocol

        :param signal_results: Voltage signals to analyze
        :type signal_results: Iterable[AnalysedSignal]
        :return: Aggregated signal groups
        :rtype: Iterable[SignalGroup]
        """
        list_of_signal_groups = []

        periodic_related_groups = \
            cls.__get_periodic_related_groups(signal_results)
        standalone_lines = \
            cls.__generate_standalone_line_groups(signal_results)
        list_of_signal_groups.extend(periodic_related_groups)
        list_of_signal_groups.extend(standalone_lines)
        cls.log.debug("Overall amount of found signal groups: %d",
                      len(list_of_signal_groups))
        return list_of_signal_groups

    @classmethod
    def __retrieve_single_signal(cls, signal, list_of_measured_signals):
        periodic_signal = copy(signal)
        list_of_measured_signals.remove(signal)
        return periodic_signal

    @classmethod
    def __retrieve_periodic_signals(cls, list_of_measured_signals):
        list_of_periodic_signals = []
        for signal in list_of_measured_signals:
            if signal.event_properties.signal_type == SignalType.PERIODIC:
                periodic_signal = cls.__retrieve_single_signal(signal,
                                                               list_of_measured_signals)
                list_of_periodic_signals.append(periodic_signal)

        list_of_periodic_signals = cls.__sort_signals(list_of_periodic_signals)
        cls.log.debug("Amount of found periodic signals: %d",
                      len(list_of_periodic_signals))
        return list_of_periodic_signals

    @classmethod
    def __is_runtime_correlated(cls, psignal, msignal):
        msignal_activity = msignal.event_properties.transmission_activity_list
        psignal_activity = psignal.event_properties.transmission_activity_list
        same_activity_amount = \
            len(msignal_activity) == len(psignal_activity)
        msignal_index = msignal.signal.index
        psignal_index = psignal.signal.index
        if same_activity_amount:
            all_same_signal_activity_durations = True
            overall_duration_rating = 1
            for i, activity in enumerate(msignal_activity):
                msignal_start = activity[0]
                msignal_end = activity[1]

                psignal_start = psignal_activity[i][0]
                psignal_end = psignal_activity[i][1]

                if psignal.event_properties.double_event_duration is not None:
                    psignal_period = psignal.event_properties.double_event_duration
                elif psignal.event_properties.first_reoccuring_duration is not None:
                    psignal_period = psignal.event_properties.first_reoccuring_duration * 2
                else:
                    return False, 0

                similar_signal_activity_durations = (
                    (msignal_start > psignal_start - psignal_period)
                    and
                    (msignal_end < psignal_end + psignal_period)
                )
                if not similar_signal_activity_durations:
                    all_same_signal_activity_durations = False
                psignal_duration = (psignal_end-psignal_start)
                msignal_duration = (msignal_end - msignal_start)
                this_duration_rating = psignal_duration / msignal_duration
                overall_duration_rating = \
                    overall_duration_rating * this_duration_rating
                cls.log.debug(("Overall duration rating between psignal with "
                               "index %s and msignal with %s based on activity = %s"),
                              psignal_index, msignal_index, overall_duration_rating)
            return all_same_signal_activity_durations, overall_duration_rating

        return False, 0

    @classmethod
    def __periodic_burst_cycletime_correlation(cls, psignal, msignal):
        msignal_symbol = msignal.event_properties.first_reoccuring_duration
        psignal_period = psignal.event_properties.double_event_duration
        psignal_period_frac = psignal.event_properties.first_reoccuring_duration

        if msignal_symbol is None:
            return False

        activity_correlation = ((psignal_period - psignal_period_frac)
                                < msignal_symbol <
                                (psignal_period + psignal_period_frac))

        activity_correlation_rating = msignal_symbol / psignal_period
        msignal_index = msignal.signal.index
        psignal_index = psignal.signal.index
        cls.log.debug(("Cycletime_correlation_rating between periodic signal "
                       "%s and message signal %s: %s"),
                      psignal_index, msignal_index, activity_correlation_rating)
        return activity_correlation, activity_correlation_rating

    @ classmethod
    def __periodic_burst_correlation_check(cls, periodic_signal, measured_signal):
        psignal = periodic_signal
        msignal = measured_signal

        runtime_correlation, overall_duration_rating = \
            cls.__is_runtime_correlated(psignal, msignal)
        cls.log.debug("Runtimes are correlated: %s", runtime_correlation)

        activity_cycles_correlation, activity_correlation_rating = \
            cls.__periodic_burst_cycletime_correlation(psignal, msignal)
        cls.log.debug("Cycle durations are correlated: %s",
                      activity_cycles_correlation)

        correlation = runtime_correlation and activity_cycles_correlation
        correlation_rating = overall_duration_rating * activity_correlation_rating
        return correlation, correlation_rating

    @ classmethod
    def __group_periodic_burst_related_signals(cls, list_of_periodic_signals,
                                               list_of_measured_signals):
        # Empty list, where the correlation ratings for the
        # link between the clock signal and each data signal
        correlated_signals_groups = []
        for psignal in list_of_periodic_signals:
            correlated_signals = []
            correlated_signals.append(psignal)
            correlation_rating_list = []
            for msignal in list_of_measured_signals:
                correlated, correlation_rating = cls.__periodic_burst_correlation_check(
                    psignal, msignal)
                if correlated:
                    corr_signal = cls.__retrieve_single_signal(msignal,
                                                               list_of_measured_signals)
                    correlated_signals.append(corr_signal)
                    correlation_rating_list.append(correlation_rating)
            new_signal_group = SignalGroup(correlated_signals)
            # Takes the last "correlated rating" here and applies
            # it to the signal group.
            if len(correlation_rating_list) > 0:
                new_signal_group.correlation_rating = correlation_rating_list[-1]
            else:
                new_signal_group.correlation_rating = None
            cls.log.debug('Amount of lines in clock-data correlated signal groups %d',
                          len(correlated_signals))
            correlated_signals_groups.append(new_signal_group)
            del new_signal_group
            del correlated_signals
            del correlation_rating_list
        cls.log.debug('Amount of clock-data correlated signal groups %d',
                      len(correlated_signals_groups))
        return correlated_signals_groups

    @classmethod
    def __get_periodic_related_groups(cls, list_of_measured_signals):
        list_of_periodic_signals = \
            cls.__retrieve_periodic_signals(
                list_of_measured_signals)
        periodic_burst_correlation_groups = \
            cls.__group_periodic_burst_related_signals(
                list_of_periodic_signals,
                list_of_measured_signals)
        return periodic_burst_correlation_groups

    @classmethod
    def __generate_standalone_line_groups(cls, list_of_measured_signals):
        correlated_signals_groups = []
        for signal in list_of_measured_signals:
            correlated_signals = []
            no_periodic_signal = None
            correlated_signals.append(no_periodic_signal)
            correlated_signals.append(signal)
            new_signal_group = SignalGroup(correlated_signals)
            new_signal_group.protocol_name = signal.event_properties.signal_type
            correlated_signals_groups.append(new_signal_group)
            del new_signal_group
            del correlated_signals
        cls.log.debug('Amount of standalone signal groups %d',
                      len(correlated_signals_groups))
        return correlated_signals_groups

    @staticmethod
    def __get_max_duration(signals_list):
        max_duration = 0
        for signal in signals_list:
            signal_duration = signal.signal.measurement_duration
            if signal_duration > max_duration:
                max_duration = signal_duration
        return max_duration

    @staticmethod
    def __get_signal_of_duration(signals_list, duration):
        for signal in signals_list:
            if duration == signal.signal.measurement_duration:
                return signal
        print(f"WARNING! Signal for duration {duration} not found in list")
        return None

    @classmethod
    def __get_signal_with_longtest_duration(cls, signals_list):
        max_duration = cls.__get_max_duration(signals_list)
        longest_signal = cls.__get_signal_of_duration(
            signals_list, max_duration)
        return longest_signal

    @classmethod
    def __sort_signals(cls, signals_list):
        sorted_list = []

        while len(signals_list) > 0:
            longest_signal = cls.__get_signal_with_longtest_duration(
                signals_list)
            if longest_signal is not None:
                signal = copy(longest_signal)
                signals_list.remove(longest_signal)
                sorted_list.append(signal)
        sorted_list.reverse()

        return sorted_list
