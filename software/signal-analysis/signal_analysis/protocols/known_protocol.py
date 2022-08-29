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

from abc import ABC, abstractmethod


from signal_analysis. model import SignalGroup


class KnownProtocol(ABC):
    """
    Base class for all known bus protocols
    """

    def __init__(self, name: str):
        self.__name = name

    @property
    def name(self) -> str:
        """
        Return the protocol name
        """
        return self.__name

    @name.setter
    def name(self, name: str) -> None:
        self.__name = name

    @abstractmethod
    def identify_parameters(self, signal_group: SignalGroup) -> dict:
        """
        Determine additional protocol parameters based on a signal group

        :param signal_group: Signal group to analyse
        :type signal_group: SignalGroup
        :return: Determined protocol parameters, defaults to None.
        :rtype: dict
        """

    @abstractmethod
    def rate_signal_group(self, signal_group: SignalGroup) -> int:
        """
        Determine a rating value based on signal characteristics that indicate
        how likely the signal group has been produced by the current protocol

        :param signal_group: Signal group to rate
        :type signal_group: SignalGroup
        :return: Rating value in the range of [0, 10] with a value of 10 indicating
                 a high probability that the signal group matches the protocol
        :rtype: int
        """
