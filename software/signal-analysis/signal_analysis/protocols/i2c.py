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
from .rating_utils import has_minimum_num_voltage_levels, is_voltage_in_range, \
    is_transmission_speed_faster_than, check_voltage_widths, \
    is_longest_voltage_level_in_range, is_block_duration_in_range


class I2C(KnownProtocol):
    """
    Inter-Integrated Circuit (I2C) protocol
    """

    def __init__(self):
        KnownProtocol.__init__(self, "I2C")

    def identify_parameters(self, _: SignalGroup) -> dict:
        return {}

    def rate_signal_group(self, signal_group: SignalGroup) -> int:
        rating_result = 0

        # Rate I2C CLK line
        i2c_clk = signal_group.analyzed_signals[0] \
            if len(signal_group.analyzed_signals) > 0 else None
        if i2c_clk is not None:
            rating_result += self.__rate_as_i2c_clk_line(i2c_clk)
        else:
            rating_result -= 5

        # Rate I2C SDA line
        i2c_sda = signal_group.analyzed_signals[1] \
            if len(signal_group.analyzed_signals) > 1 else None
        if i2c_sda is not None:
            rating_result += self.__rate_as_i2c_sda_line(i2c_sda)
        else:
            rating_result -= 5

        return floor(rating_result)

    @ staticmethod
    def __rate_as_i2c_clk_line(signal: AnalysedSignal) -> int:
        rating_counter = has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 5500)
        rating_counter += check_voltage_widths(signal, 5, 20)
        rating_counter += is_transmission_speed_faster_than(signal, 100)
        rating_counter += is_longest_voltage_level_in_range(signal, 0.9, 1.1)
        rating_counter += is_block_duration_in_range(signal, 9, 9.5)
        return rating_counter * 5/6

    @ staticmethod
    def __rate_as_i2c_sda_line(signal: AnalysedSignal) -> int:
        rating_counter = has_minimum_num_voltage_levels(signal, 2)
        rating_counter += is_voltage_in_range(signal, -100, 5500)
        rating_counter += check_voltage_widths(signal, 10, 5)
        rating_counter += is_transmission_speed_faster_than(signal, 100)
        rating_counter += is_longest_voltage_level_in_range(signal, 0.9, 1.1)
        rating_counter += is_block_duration_in_range(signal, 9, 9.5)
        return rating_counter * 5/6
