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

from math import floor

from signal_analysis.model import SignalGroup, AnalysedSignal

from .known_protocol import KnownProtocol
from .spi_parameter_identifier import SpiParameterIdentifier

from .rating_utils import has_minimum_num_voltage_levels, is_voltage_in_range, \
    is_transmission_speed_faster_than, is_block_duration_in_range, \
    are_voltage_widths_larger_than, is_longest_voltage_level_in_range


class Spi(KnownProtocol):
    """
    Serial Peripheral Interface (SPI) protocol
    """

    def __init__(self):
        KnownProtocol.__init__(self, "SPI")

    def identify_parameters(self, signal_group: SignalGroup) -> dict:
        return SpiParameterIdentifier.parameters(signal_group)

    def rate_signal_group(self, signal_group: SignalGroup) -> int:
        rating_result = 0

        # Rate SPI CLK line
        spi_clk = signal_group.analyzed_signals[0] \
            if len(signal_group.analyzed_signals) > 0 else None
        if spi_clk is not None:
            rating_result += self.__rate_as_spi_clk_line(spi_clk)
        else:
            rating_result -= 5

        # Rate SPI MOSI line
        spi_mosi = signal_group.analyzed_signals[1] \
            if len(signal_group.analyzed_signals) > 1 else None
        if spi_mosi is not None:
            rating_result += self.__rate_as_spi_mosi_line(spi_mosi)
        else:
            rating_result -= 5

        # Rate SPI MISO line
        spi_miso = signal_group.analyzed_signals[2] \
            if len(signal_group.analyzed_signals) > 2 else None
        if spi_miso is not None:
            rating_result += self.__rate_as_spi_miso_line(spi_miso)
        else:
            rating_result -= 5

        return rating_result

    @classmethod
    def __rate_as_spi_clk_line(cls, signal: AnalysedSignal) -> int:
        rating_counter = has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 6000)
        rating_counter += are_voltage_widths_larger_than(signal, 5, 20)
        rating_counter += is_transmission_speed_faster_than(signal, 4)
        rating_counter += is_longest_voltage_level_in_range(signal,
                                                            0.9, 1.1,
                                                            0.1, 0.9)
        rating_counter += is_block_duration_in_range(signal, 7, 7.5)
        rating_counter += cls.__rate_voltage_state_duration_symmetry(
            signal)
        return floor(rating_counter * 5/7)

    @staticmethod
    def __rate_as_spi_miso_line(signal: AnalysedSignal) -> int:
        rating_counter = has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 6000)
        rating_counter += are_voltage_widths_larger_than(signal, 10, 5)
        rating_counter += is_transmission_speed_faster_than(signal, 4)
        rating_counter += is_longest_voltage_level_in_range(signal,
                                                            0.4, 0.6,
                                                            0.1, 0.9)
        rating_counter += is_block_duration_in_range(signal, 7, 7.5)
        return floor(rating_counter * 5/6)

    @staticmethod
    def __rate_as_spi_mosi_line(signal: AnalysedSignal) -> int:
        rating_counter = 0
        rating_counter += has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 6000)
        rating_counter += are_voltage_widths_larger_than(signal, 10, 5)
        rating_counter += is_transmission_speed_faster_than(signal, 4)
        rating_counter += is_longest_voltage_level_in_range(signal, 0.9, 1.1)
        rating_counter += is_block_duration_in_range(signal, 7, 7.5)
        return floor(rating_counter * 5/6)

    @staticmethod
    def __rate_voltage_state_duration_symmetry(signal_line: AnalysedSignal) -> int:
        """
        According to SPI-Spec:
            t(U_low)    = 0.45 * Tperiod
            t(U_high)   = 0.45 * Tperiod
        """
        duration_voltage_state = signal_line.event_properties.first_reoccuring_duration
        duration_period = signal_line.event_properties.double_event_duration
        lower_limit = 0.9 * duration_voltage_state
        upper_limit = 1.1 * duration_voltage_state
        if lower_limit <= duration_period / 2 <= upper_limit:
            return 1

        lower_limit = 0.6 * duration_voltage_state
        upper_limit = 1.4 * duration_voltage_state
        if lower_limit <= duration_period / 2 <= upper_limit:
            return 0
        return -1
