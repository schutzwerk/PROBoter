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

from signal_analysis.model import SignalGroup, AnalysedSignal

from .known_protocol import KnownProtocol
from .rating_utils import has_num_voltage_levels, is_voltage_in_range, \
    has_num_single_event_peaks, are_voltage_widths_lower_than, \
    has_no_transmission_blocks, are_state_durations_not_int_multiple, \
    has_num_event_pairs


class OneWire(KnownProtocol):
    """
    One wire protocol
    """

    def __init__(self):
        KnownProtocol.__init__(self, "OneWire")

    def identify_parameters(self, _: SignalGroup) -> dict:
        return {}

    def rate_signal_group(self, signal_group: SignalGroup) -> float:
        rating_result = 0
        # Check if the signal group contains more than a clock
        # and a single data line and if no clock line could be identified
        if len(signal_group.analyzed_signals) > 2 \
                or signal_group.analyzed_signals[0] is not None:
            rating_result -= 5

        # Rate the one wire data line
        data_line = signal_group.analyzed_signals[1] \
            if len(signal_group.analyzed_signals) > 1 else None
        if data_line is not None:
            rating_result += self.__rate_as_one_wire_line(data_line)

        return rating_result * 2

    @ classmethod
    def __rate_as_one_wire_line(cls, signal: AnalysedSignal) -> int:
        rating_counter = has_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, 0, 32000)
        rating_counter += are_voltage_widths_lower_than(signal, 5, 5)
        rating_counter += has_num_single_event_peaks(signal, 4)
        rating_counter += has_num_event_pairs(signal, 1, 2)
        rating_counter += cls.__absence_of_pattern(signal)
        rating_counter += has_no_transmission_blocks(signal)
        rating_counter += are_state_durations_not_int_multiple(signal)
        return rating_counter * 5/8

    @ classmethod
    def __absence_of_pattern(cls, signal_line):
        repeating_pattern_duration = signal_line.pattern_properties.repeating_pattern_duration_ns
        if (repeating_pattern_duration is None) or (repeating_pattern_duration > 20):
            return 1
        return 0
