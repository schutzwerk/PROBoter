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

from signal_analysis.model import AnalysedSignal


def has_num_voltage_levels(signal_line: AnalysedSignal, num_levels: int) -> int:
    if len(signal_line.voltage_properties.main_voltage_levels) == num_levels:
        return 1
    return -1


def has_minimum_num_voltage_levels(signal_line: AnalysedSignal, num_levels: int) -> int:
    if len(signal_line.voltage_properties.main_voltage_levels) == num_levels:
        return 1
    if len(signal_line.voltage_properties.main_voltage_levels) > 2:
        return 0
    return -1


def is_voltage_in_range(signal_line: AnalysedSignal, min_voltage: float, max_voltage: float) -> int:
    if (signal_line.voltage_properties.main_voltage_levels[0] >= min_voltage) \
            and (signal_line.voltage_properties.main_voltage_levels[-1] <= max_voltage):
        return 1
    return 0


def is_transmission_speed_faster_than(signal_line: AnalysedSignal,
                                      min_speed: float) -> int:
    if signal_line.event_properties.double_event_duration is None:
        return -1
    if signal_line.event_properties.double_event_duration >= min_speed:
        return 1
    return 0


def check_voltage_widths(signal_line: AnalysedSignal,
                         low_volt_min: float, high_volt_max: float) -> int:
    voltage_properties = signal_line.voltage_properties
    if (voltage_properties.relative_width_of_lowest_voltage_level >= low_volt_min) \
            and (voltage_properties.relative_width_of_upper_voltage_level < high_volt_max):
        return 1
    if (voltage_properties.relative_width_of_lowest_voltage_level >= low_volt_min) \
            or (voltage_properties.relative_width_of_upper_voltage_level < high_volt_max):
        return 0
    return -1


def are_voltage_widths_larger_than(signal_line: AnalysedSignal,
                                   low_volt_min: float, high_volt_min: float) -> int:
    voltage_properties = signal_line.voltage_properties
    if (voltage_properties.relative_width_of_lowest_voltage_level >= low_volt_min) \
            and (voltage_properties.relative_width_of_upper_voltage_level >= high_volt_min):
        return 1
    if (voltage_properties.relative_width_of_lowest_voltage_level >= low_volt_min) \
            or (voltage_properties.relative_width_of_upper_voltage_level >= high_volt_min):
        return 0
    return -1


def are_voltage_widths_lower_than(signal_line: AnalysedSignal,
                                  low_volt_min: float, high_volt_min: float) -> int:
    voltage_properties = signal_line.voltage_properties
    if (voltage_properties.relative_width_of_lowest_voltage_level <= low_volt_min) \
            and (voltage_properties.relative_width_of_upper_voltage_level <= high_volt_min):
        return 1
    if (voltage_properties.relative_width_of_lowest_voltage_level <= low_volt_min) \
            or (voltage_properties.relative_width_of_upper_voltage_level <= high_volt_min):
        return 0
    return -1


def is_longest_voltage_level_in_range(signal_line: AnalysedSignal,
                                      min_percentage: float = 0.9,
                                      max_percentage: float = 1.1,
                                      tolerated_min_percentage: float = None,
                                      tolerated_max_percentage: float = None) -> int:
    upper_voltage_level = signal_line.voltage_properties.main_voltage_levels[-1]
    lower_limit = min_percentage * upper_voltage_level
    upper_limit = max_percentage * upper_voltage_level
    if lower_limit <= signal_line.event_properties.voltage_of_longest_duration <= upper_limit:
        return 1

    if tolerated_min_percentage is not None \
            and tolerated_max_percentage is not None:
        lower_limit = tolerated_min_percentage * upper_voltage_level
        upper_limit = tolerated_max_percentage * upper_voltage_level
        if lower_limit <= signal_line.event_properties.voltage_of_longest_duration <= upper_limit:
            return 0
    return -1


def is_block_duration_in_range(signal_line: AnalysedSignal,
                               min_duration: float = 9, max_duration: float = 9.5) -> int:
    if signal_line.event_properties.transmission_block_duration is None:
        return 0

    block_duration = signal_line.event_properties.transmission_block_duration
    lower_duration_limit = signal_line.event_properties.double_event_duration * min_duration
    upper_duration_limit = signal_line.event_properties.double_event_duration * max_duration
    if lower_duration_limit < block_duration < upper_duration_limit:
        return 1
    return -1


def has_num_single_event_peaks(signal_line: AnalysedSignal, num_peaks: int) -> int:
    amount_peaks = signal_line.event_properties.amount_reoccuring_durations
    if amount_peaks == num_peaks:
        return 1
    return -1


def has_transmission_blocks(signal_line: AnalysedSignal) -> int:
    if signal_line.event_properties.transmission_block_duration is not None:
        return 1
    return 0


def has_no_transmission_blocks(signal_line: AnalysedSignal) -> int:
    if signal_line.event_properties.transmission_block_duration is None:
        return 1
    return 0


def are_state_durations_int_multiple(signal_line: AnalysedSignal) -> int:
    if signal_line.event_properties.are_state_durations_int_multiple:
        return 1
    return 0


def are_state_durations_not_int_multiple(signal_line: AnalysedSignal) -> int:
    if not signal_line.event_properties.are_state_durations_int_multiple:
        return 1
    return 0


def has_num_event_pairs(signal_line: AnalysedSignal, num_pairs: int,
                        num_tolerated_pairs: int = None) -> int:
    amount_event_pair_peaks = signal_line.event_properties.amount_of_event_pairs
    if amount_event_pair_peaks == num_pairs:
        return 1
    if num_tolerated_pairs is not None \
            and amount_event_pair_peaks == num_tolerated_pairs:
        return 0
    return -1


def are_event_durations_symmetric(signal_line: AnalysedSignal) -> int:
    if signal_line.event_properties.event_duration_symmetry:
        return 1
    return 0


def are_repeating_patterns_in_range(signal_line: AnalysedSignal,
                                    min_duration: int, max_duration: int) -> int:
    pattern_duration = signal_line.pattern_properties.repeating_pattern_duration_symbols
    if pattern_duration is None:
        return -1
    if min_duration <= pattern_duration <= max_duration:
        return 1
    return 0
