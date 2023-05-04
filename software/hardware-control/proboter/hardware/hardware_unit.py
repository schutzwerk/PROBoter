# Copyright (C) 2023 SCHUTZWERK GmbH
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
from typing import TypeVar, Generic

S = TypeVar('S')
T = TypeVar('T')


class HardwareUnit(ABC, Generic[S, T]):
    """
    Base class for all individual hardware units
    """

    def __init__(self, config: S, status: T) -> None:
        """
        Initialize a hardware unit

        :param config: Hardware unit configuration
        :type config: S
        :param status: Initial status of the unit
        :type status: T
        """
        self._config = config
        self._status = status

    @property
    def config(self) -> S:
        """
        The current hardware unit configuration

        :rtype: S
        """
        return self._config

    @property
    def status(self) -> T:
        """
        Current status of the hardware unit
        :rtype: T
        """
        return self._status

    @abstractmethod
    async def start(self) -> None:
        """
        Set up and initialize the hardware unit
        """

    @abstractmethod
    async def stop(self) -> None:
        """
        Shutdown the hardware unit
        """

    async def sync(self) -> None:
        """
        Force synchronization with the hardware's state
        """
