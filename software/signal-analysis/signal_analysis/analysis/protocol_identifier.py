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
from typing import Iterable, List

from signal_analysis.model import SignalType, SignalGroup
from signal_analysis.protocols import KnownProtocol, I2C, Spi, Uart, OneWire


class ProtocolIdentifier:
    """
    Protocol identifier
    """

    log = logging.getLogger(__name__)

    @classmethod
    def identify_protocols(cls, grouped_signals: Iterable[SignalGroup]) -> Iterable[SignalGroup]:
        """
        For each detected group of signal, identify / rate each signal group
        based on a list of known protocols

        Eventually, the known protocol which produces the highest rating
        probably is the protocol which has been used to produce the signal.

        :param grouped_signals: Grouped signals to rate
        :type grouped_signals: Iterable[SignalGroup]
        :return: Modified signal groups
        :rtype: Iterable[SignalGroup]
        """

        known_protocols = (Spi(), I2C(), Uart(), OneWire())
        known_protocol_names = [protocol.name for protocol in known_protocols]

        for signal in grouped_signals:
            if cls.__contains_clock_or_data(signal):
                # Compare the signal group with all known protocols
                rating_array = cls.__rate_signal_group(signal, known_protocols)

                # Find the protocol with the highest rating
                max_index = rating_array.index(max(rating_array))
                identified_protocol = known_protocols[max_index]

                # Set the protocol name of the signal group
                signal.protocol_name = identified_protocol.name
                cls.log.debug("Protocol found: %s", identified_protocol.name)

                # Determine additional protocl parameters
                parameters = identified_protocol.identify_parameters(signal)
                signal.encoding_parameters = parameters
                cls.log.debug("Encoding parameters: %s", parameters)

                # Build a protocol rating dict
                rating_dict = dict(zip(known_protocol_names, rating_array))
                signal.identification_ratings = rating_dict
                cls.log.debug("Rating list: %s", rating_dict)

        return grouped_signals

    @staticmethod
    def __contains_clock_or_data(signal_group: SignalGroup) -> bool:
        """
        Check if a signal groups might contain data or clock signals
        """
        for line in signal_group.analyzed_signals:
            if line is None:
                pass
            elif line.event_properties.signal_type == SignalType.PERIODIC:
                return True
            elif line.event_properties.signal_type == SignalType.BURST:
                return True
        return False

    @classmethod
    def __rate_signal_group(cls, signal_group: SignalGroup,
                            protocols: Iterable[KnownProtocol]) -> List[float]:
        """
        Produce an array with results, how well the current signal fulfiles the
        characteristics of each known protocol line
        """
        rating_array = []
        for protocol in protocols:
            rating = protocol.rate_signal_group(signal_group)
            rating = max(rating, 0)
            rating = min(rating, 10)
            rating /= 10.0
            rating_array.append(rating)
        return rating_array
