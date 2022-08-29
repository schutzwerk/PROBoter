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

from signal_analysis.model import SignalGroup
from signal_analysis.model.signal_analysis_result import AnalysedSignal


class UartParameterIdentifier:
    """
    UART parameter identifier
    """

    log = logging.getLogger(__name__)

    @classmethod
    def parameters(cls, signal_group: SignalGroup) -> dict:
        list_of_parameters = {}

        # Run evaluation
        signal = signal_group.analyzed_signals[1]
        is_inverted_signal_line = cls.__is_inverted_signal_line(signal)
        list_of_parameters["Signal inverted"] = is_inverted_signal_line
        list_of_parameters.update(cls.__get_baud_rate(signal))
        repeating_pattern_duration_symbols = \
            signal.pattern_properties.repeating_pattern_duration_symbols

        if repeating_pattern_duration_symbols is not None:
            amount_stop_bits, found_rate = \
                cls.__amount_stop_bits(signal, is_inverted_signal_line)
        else:
            amount_stop_bits = "Unknown"
            found_rate = 0

        list_of_parameters["Amount of stop bits"] = amount_stop_bits
        list_of_parameters["Find-rating for identification of stop bits"] = \
            found_rate

        if amount_stop_bits != "Unknown":
            parity_bit, found_parity_rate = \
                cls.__parity_bit_implemented(signal, amount_stop_bits,
                                             is_inverted_signal_line)
        elif amount_stop_bits == "Unknown":
            parity_bit = "Unknown"
            found_parity_rate = 0
        list_of_parameters["Parity bit implemented"] = parity_bit
        list_of_parameters["Parity-bit recognition rate"] = found_parity_rate

        # Checking for the amount of data-bits per frame:
        if amount_stop_bits != "Unknown" and parity_bit != "Unknown":
            list_of_parameters.update(cls.__amount_data_bits_per_frame(signal,
                                      amount_stop_bits, parity_bit))
        elif amount_stop_bits == "Unkown" or parity_bit == "Unkown":
            list_of_parameters["Block length"] = "Cannot be identified"
        return list_of_parameters

    @classmethod
    def __is_within_low_voltage(cls, list_of_main_voltages, default_voltage):
        low_voltage = list_of_main_voltages[0]
        high_voltage = list_of_main_voltages[-1]
        return (high_voltage - ((high_voltage - low_voltage) * 1.1)) \
            < default_voltage < \
            (high_voltage - ((high_voltage - low_voltage) * 0.9))

    @classmethod
    def __is_within_high_voltage(cls, list_of_main_voltages, default_voltage):
        low_voltage = list_of_main_voltages[0]
        high_voltage = list_of_main_voltages[-1]
        return (low_voltage + ((high_voltage - low_voltage) * 0.9)) \
            < default_voltage < \
            (low_voltage + ((high_voltage - low_voltage) * 1.1))

    @classmethod
    def __is_inverted_signal_line(cls, signal):
        default_voltage = signal.event_properties.voltage_of_longest_duration
        list_of_main_voltages = signal.voltage_properties.main_voltage_levels

        if cls.__is_within_low_voltage(list_of_main_voltages, default_voltage):
            return True
        if cls.__is_within_high_voltage(list_of_main_voltages, default_voltage):
            return False
        print("Cannot identify clock polarity. Default voltage not fitting")
        return None

    @classmethod
    def __round_baud_rate(cls, baud_rate):
        known_baud_list = [110, 300, 600, 1200, 2400, 4800, 9600, 14400, 19200,
                           38400, 57600, 115200, 128000, 256000, 500000, 1000000]
        for baud in known_baud_list:
            if baud * 0.9 < baud_rate < baud * 1.1:
                baud_recogn_rating = abs((baud_rate / baud))
                return baud, baud_recogn_rating
        return baud_rate, None

    @classmethod
    def __get_baud_rate(cls, signal):
        symbol_duration_ns = signal.event_properties.first_reoccuring_duration
        baud_rate = int(1 / symbol_duration_ns * 1e9)
        baud_rate, baud_recogn_rating = cls.__round_baud_rate(baud_rate)
        return {"Baud rate": baud_rate, "Baud rate recognition rating": baud_recogn_rating}

    @classmethod
    def __amount_stop_bits(cls, signal, inverted):
        symbol_duration_ns = signal.event_properties.first_reoccuring_duration
        binary_array = cls.__decode_uart_to_binary(signal,
                                                   symbol_duration_ns,
                                                   inverted)
        block_length_in_symbols = \
            round(signal.pattern_properties.repeating_pattern_duration_symbols)
        single_stop_bit_pattern = [1, 0]
        double_stop_bit_pattern = [1, 1, 0]

        # Limit to an area which should have a binary signal
        # Since I know that I require about 100 Bytes for identification
        # of the frame length:
        # 100 bytes * 10 symbols == 1000 symbols
        # Limit by about the half, in case we encounter shorter signals
        if len(binary_array) >= 500:
            slice_limit = 500
        elif len(binary_array) < 500:
            slice_limit = len(binary_array)

        pattern = single_stop_bit_pattern
        transmission_frame_offset, found_rate_single = \
            cls.__identify_transmission_frame_offset(
                binary_array[:slice_limit],
                block_length_in_symbols, pattern)
        single_stop = transmission_frame_offset is not None

        pattern = double_stop_bit_pattern
        transmission_frame_offset, found_rate_double = \
            cls.__identify_transmission_frame_offset(
                binary_array[:slice_limit],
                block_length_in_symbols, pattern)

        double_stop = transmission_frame_offset is not None
        if double_stop:
            return 2, found_rate_double
        if single_stop:
            return 1, found_rate_single
        return "Unknown", 0

    @classmethod
    def __parity_bit_implemented(cls, signal, amount_stop_bits, inverted):
        even = True
        odd = False
        has_even_parity, found_even_parity_rate = \
            cls.__find_parity_bit(signal, amount_stop_bits, even, inverted)

        has_odd_parity, found_odd_parity_rate = \
            cls.__find_parity_bit(signal, amount_stop_bits, odd, inverted)

        if has_odd_parity and has_even_parity:
            return "Unknown", None
        if has_odd_parity:
            return "Odd", found_odd_parity_rate
        if has_even_parity:
            return "Even", found_even_parity_rate
        return False, None

    @classmethod
    def __amount_data_bits_per_frame(cls, signal, amount_stop_bits, parity_bit):
        block_length_in_symbols = \
            round(signal.pattern_properties.repeating_pattern_duration_symbols)
        block_length_in_symbols -= 1  # due to start bit
        block_length_in_symbols -= amount_stop_bits  # due to stop bits
        if parity_bit:
            block_length_in_symbols -= 1  # for parity bit
        return {"Block length": block_length_in_symbols}

    @classmethod
    def __decode_uart_to_binary(cls, signal, symbol_duration, inverted=False):
        signal_event_interval_array = \
            signal.event_properties.signed_interval_array
        array_of_binary = []
        for signal_event_interval in signal_event_interval_array:
            symbol_amount = cls.__amount_of_symbols(
                signal_event_interval,
                symbol_duration)
            symbol = cls.__get_logic_level(signal_event_interval)
            block = [symbol] * symbol_amount
            array_of_binary.extend(block)
        if inverted:
            cls.log.debug("Inverting binary signals")
            array_of_binary = [(binary - 1) * (-1)
                               for binary in array_of_binary]
        return array_of_binary

    @classmethod
    def __identify_transmission_frame_offset(cls, array_of_binary,
                                             block_length_symbols, pattern):
        length_reoccuring_pattern = len(pattern)
        cls.log.debug("Array of binary: %s", array_of_binary)
        for offset in range(int(0.5 * len(array_of_binary))):
            search_limit = int(
                0.5 * (len(array_of_binary) - length_reoccuring_pattern + 1))
            pattern_found = 0
            for i in range(0, search_limit, block_length_symbols):
                if pattern == array_of_binary[offset + i:length_reoccuring_pattern + offset + i]:
                    pattern_found += 1
            offset_rating = pattern_found / \
                len(range(0, search_limit, block_length_symbols))
            if offset_rating > 0.9:
                cls.log.debug("Offset found: %f", offset +
                              length_reoccuring_pattern)
                return (offset + length_reoccuring_pattern), offset_rating

        return None, 0

    @classmethod
    def __find_parity_bit(cls, signal: AnalysedSignal, amount_stop_bits, parity, inverted):
        symbol_duration_ns = signal.event_properties.first_reoccuring_duration
        signal_as_binary_array = \
            cls.__decode_uart_to_binary(signal, symbol_duration_ns, inverted)

        if len(signal_as_binary_array) >= 500:
            slice_limit = 500
        elif len(signal_as_binary_array) < 500:
            slice_limit = len(signal_as_binary_array)
        signal_as_binary_array = signal_as_binary_array[:slice_limit]
        cls.log.debug("Signal as binary array: %s", signal_as_binary_array)

        block_length_in_symbols = \
            round(signal.pattern_properties.repeating_pattern_duration_symbols)
        frame_offset = \
            cls.__get_offset_for_frame_subdivision(signal_as_binary_array,
                                                   block_length_in_symbols,
                                                   amount_stop_bits)
        if frame_offset is None:
            cls.log.debug("Frame offset is None")
            return None

        length_reoccuring_pattern = amount_stop_bits + 1
        array_of_frames = \
            cls.__get_array_of_transmission_frames(
                signal_as_binary_array, block_length_in_symbols,
                length_reoccuring_pattern, frame_offset)
        sufficient_framelength = all((len(frame) >= 5)
                                     for frame in array_of_frames)
        if sufficient_framelength:
            amount_found_parity = 0
            # Parity "lookup":
            even = True
            odd = False
            ####
            if parity == even:
                for frame in array_of_frames:
                    if (sum(frame[:-1]) % 2) == frame[-1]:
                        amount_found_parity += 1
            elif parity == odd:
                for frame in array_of_frames:
                    if (sum(frame[:-1]) % 2) != frame[-1]:
                        amount_found_parity += 1
            found_parity_rate = amount_found_parity / len(array_of_frames)
            found_parity = found_parity_rate >= 0.9
        else:
            cls.log.debug("Insufficient frame length for parity bit")
            return None
        cls.log.debug("Found even parity: %s", found_parity)
        return found_parity, found_parity_rate

    @classmethod
    def __amount_of_symbols(cls, event, symbol_duration):
        amount = abs(round(event / symbol_duration))
        return amount

    @classmethod
    def __get_logic_level(cls, symbols):
        if symbols > 0:
            return 0
        return 1

    @classmethod
    def __get_array_of_transmission_frames(cls, signal_as_binary_array,
                                           block_length_in_symbols,
                                           length_reoccuring_pattern,
                                           offset):
        array_of_frames = []
        signal_as_binary_array = signal_as_binary_array.copy()
        signal_as_binary_array = signal_as_binary_array[offset:]
        stoplimit = int(len(signal_as_binary_array)/2)
        length = block_length_in_symbols
        for _ in range(0, stoplimit, length):
            block_buffer = signal_as_binary_array[0:(length -
                                                     length_reoccuring_pattern)]
            array_of_frames.append(block_buffer)
            signal_as_binary_array = signal_as_binary_array[length:]
        cls.log.debug("Array of frames: %s", array_of_frames)
        return array_of_frames

    @classmethod
    def __get_offset_for_frame_subdivision(cls, signal_as_binary_array,
                                           block_length_in_symbols,
                                           amount_stop_bits):
        frame_offset = None
        if amount_stop_bits == 1:
            pattern = [1, 0]
            frame_offset, _ = \
                cls.__identify_transmission_frame_offset(
                    signal_as_binary_array,
                    block_length_in_symbols,
                    pattern)
        elif amount_stop_bits == 2:
            pattern = [1, 1, 0]
            frame_offset, _ = \
                cls.__identify_transmission_frame_offset(
                    signal_as_binary_array,
                    block_length_in_symbols,
                    pattern)
        return frame_offset
