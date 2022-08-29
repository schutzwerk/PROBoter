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


class SpiParameterIdentifier:
    """
    SPI protocol parameter identifier
    """

    log = logging.getLogger(__name__)

    @classmethod
    def parameters(cls, signal_group):
        parameters = {}
        if len(signal_group.analyzed_signals) >= 2:
            if (signal_group.analyzed_signals[0] is not None) \
                    and (signal_group.analyzed_signals[1] is not None):
                parameters.update(cls.__clock_polarity(signal_group))
                parameters.update(cls.__clock_phase(signal_group))
        return parameters

    @classmethod
    def __get_clock_interval_data(cls, signal_group):
        clock_signal = signal_group.analyzed_signals[0]
        if clock_signal is None:
            cls.log.warning(
                "Cannot identify SPI parameters. Clock data missing!")
            return None
        return clock_signal.event_properties.interval_array

    @classmethod
    def __get_clock_symbol_duration(cls, signal_group):
        clock_signal = signal_group.analyzed_signals[0]
        if clock_signal is None:
            cls.log.warning(
                "Cannot identify SPI parameters. Clock data missing!")
            return None
        return clock_signal.event_properties.first_reoccuring_duration

    @classmethod
    def __get_data_interval_data(cls, signal_group):
        data_signal = signal_group.analyzed_signals[1]
        if data_signal is None:
            cls.log.warning(
                "Cannot identify SPI parameters. Transmission data missing!")
            return None
        return data_signal.event_properties.interval_array

    @classmethod
    def __get_overall_durations(cls, interval_array, offset, stepwidth):
        filtered_array = []
        for i in range(offset, int(len(interval_array) / 1000), stepwidth):
            time_sum = sum(interval_array[:i])
            filtered_array.append(time_sum)
        return filtered_array

    @classmethod
    def __amount_coinciding_events(cls, clock_durations, symbol_duration,
                                   data_durations):

        if len(clock_durations) <= 0 or len(data_durations) <= 0:
            return 0

        counter = 0
        i = 0
        for clock_timestamp in clock_durations:
            lower_timelimit = clock_timestamp - (symbol_duration / 2)
            upper_timelimit = clock_timestamp + (symbol_duration / 2)

            while (i < len(data_durations) - 1) \
                    and (data_durations[i] <= lower_timelimit):
                i += 1
            if lower_timelimit <= data_durations[i] <= upper_timelimit:
                counter += 1
        return counter

    @classmethod
    def __clock_phase(cls, signal_group):
        """
        At the time of change of the clock signal level,
        the data signal has to be stable == the data signal
        must not change.
        This function checks, if the data signal changes around
        the time of the first and odd numbered clock changes (CPHA = 1)
        or the second and even numbered clock changes (CPHA = 0)
        See figures 4-2 and 4-3 in the SPI spec for drawings
        """
        clock = cls.__get_clock_interval_data(signal_group)
        clock_symbol_duration = cls.__get_clock_symbol_duration(signal_group)
        data = cls.__get_data_interval_data(signal_group)

        even_clock_durations = cls.__get_overall_durations(clock, 0, 2)
        odd_clock_durations = cls.__get_overall_durations(clock, 1, 2)
        data_durations = cls.__get_overall_durations(data, 0, 1)
        counter_even = cls.__amount_coinciding_events(
            even_clock_durations,
            clock_symbol_duration,
            data_durations)
        counter_odd = cls.__amount_coinciding_events(
            odd_clock_durations,
            clock_symbol_duration,
            data_durations)
        counter_sum = counter_even + counter_odd
        if counter_even > counter_odd:
            counter_fraction = 1 - (counter_odd / counter_sum)
            cls.log.debug("Clock phase 0, Clock phase fraction %s",
                          counter_fraction)
            return {"Clockphase CPHA": "0", "Clock phase fraction": counter_fraction}

        if counter_even < counter_odd:
            counter_fraction = 1 - (counter_even / counter_sum)
            cls.log.debug("Clock phase 1, Clock phase fraction %s",
                          counter_fraction)
            return {"Clockphase CPHA": "1", "Clock phase fraction": counter_fraction}

        cls.log.warning(
            "Cannot identify phase parameter. Data are rubbish")
        return None

    @classmethod
    def __is_within_low_voltage(cls, voltage_list, default_voltage):
        low_voltage = voltage_list[0]
        high_voltage = voltage_list[-1]
        return high_voltage - (high_voltage - low_voltage) * 0.9 \
            < default_voltage < high_voltage - (high_voltage - low_voltage) * 1.1

    @classmethod
    def __is_within_high_voltage(cls, voltage_list, default_voltage):
        low_voltage = voltage_list[0]
        high_voltage = voltage_list[-1]
        return low_voltage + (high_voltage - low_voltage) * 0.9 \
            < default_voltage < low_voltage + (high_voltage - low_voltage) * 1.1

    @ classmethod
    def __clock_polarity(cls, signal_group):
        clock_line = signal_group.analyzed_signals[0]
        if clock_line is None:
            return {}

        default_voltage = clock_line.event_properties.voltage_of_longest_duration
        list_of_present_voltages = clock_line.voltage_properties.main_voltage_levels

        if cls.__is_within_low_voltage(list_of_present_voltages, default_voltage):
            return {"Clock polarity CPOL": "0"}
        if cls.__is_within_high_voltage(list_of_present_voltages, default_voltage):
            return {"Clock polarity CPOL": "1"}
        print("Cannot identify clock polarity. Default voltage not fitting")
        return {}
