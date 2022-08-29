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
from .uart_parameter_identifier import UartParameterIdentifier

from .rating_utils import has_minimum_num_voltage_levels, is_voltage_in_range, \
    are_voltage_widths_lower_than, has_no_transmission_blocks, \
    are_state_durations_int_multiple, are_event_durations_symmetric, \
    are_repeating_patterns_in_range


class Uart(KnownProtocol):
    """
    Universal Asynchronous Receiver Transmitter (UART) protocol
    """

    def __init__(self):
        KnownProtocol.__init__(self, "UART")

    def identify_parameters(self, signal_group: SignalGroup) -> dict:
        return UartParameterIdentifier.parameters(signal_group)

    def rate_signal_group(self, signal_group: SignalGroup) -> float:
        rating_result = 0

        # Check if the signal group contains more than a clock
        # and two data lines and if no clock line could be identified
        if len(signal_group.analyzed_signals) > 3 \
                or signal_group.analyzed_signals[0] is not None:
            rating_result -= 5

        # Rate UART TX line
        uart_tx = signal_group.analyzed_signals[1] \
            if len(signal_group.analyzed_signals) > 1 else None
        if uart_tx is not None:
            rating_result += self.__rate_as_uart_line(uart_tx)
        else:
            rating_result -= 5

        uart_rx = signal_group.analyzed_signals[2] \
            if len(signal_group.analyzed_signals) > 2 else None
        if uart_rx is not None:
            rating_result += self.__rate_as_uart_line(uart_rx)

        return rating_result * 2

    @staticmethod
    def __rate_as_uart_line(signal: AnalysedSignal) -> int:
        rating_counter = has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 15000)
        # Found width of 13 for 1MBaud
        # Found width of 7 for 500kBaud
        # Found width of 5 for 115200 Baud
        # and
        # Found width of 5 for 1MBaud
        # Found width of 5 for 500kBaud
        # Found width of 5 for 115200 Baud
        rating_counter += are_voltage_widths_lower_than(signal, 10, 5)
        # 5 data + 1 start + stop bit
        # and 8 data + 1 start + 2 stop + 1 parity
        rating_counter += are_repeating_patterns_in_range(signal, 7, 12)
        rating_counter += has_no_transmission_blocks(signal)
        rating_counter += are_event_durations_symmetric(signal)
        rating_counter += are_state_durations_int_multiple(signal)
        rating_counter = rating_counter * 5/7
        return rating_counter
