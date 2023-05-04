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

from typing import Iterable
from abc import ABC, abstractmethod

from proboter.model import PicoscopeMeasurement

from .events import PicoscopeStatus


class Picoscope(ABC):
    """
    Interface to trigger voltage signal measurements using
    a pico Technology Picoscop oscilloscopes

    https://www.picotech.com/products/oscilloscope
    """

    @property
    @abstractmethod
    def id(self) -> int:
        """
        Return the unique identifier of the Picoscope
        """

    @property
    @abstractmethod
    def status(self) -> PicoscopeStatus:
        """
        Return the current probe status
        """

    @property
    @abstractmethod
    def device_name(self) -> str:
        """
        Return the name of the connected / configured Picoscope device
        """

    @property
    @abstractmethod
    def number_of_channels(self) -> int:
        """
        Return the number of available measurement channels
        """

    @abstractmethod
    def start(self) -> None:
        """
        Initialize and setup the connection to the Picoscope
        """

    @abstractmethod
    def stop(self) -> None:
        """
        Close the connection to the Picoscope and free all blocked resources
        """

    @abstractmethod
    def get_channel_name(self, channel_index: int) -> str:
        """
        Return the displayable name for a given channel

        :param channel_index: Channel index
        :type channel_index: int
        :return: Displayable channel name
        :rtype: str
        """

    @abstractmethod
    def take_voltage_measurement(self, time_resolution: int,
                                 number_of_samples: int,
                                 channel_indices: Iterable[int]) \
            -> Iterable[PicoscopeMeasurement]:
        """
        Take a voltage measurement with a given set of the available channels

        TODO Add parameter(s) to configure the trigger

        This method blocks until the measurement is finished!

        :param time_resolution: Time resolution in nanoseconds
        :type time_resolution: int
        :param number_of_samples: Number of samples to take. The measurement
                                  length is defined as follows:
                                  t = time_resolution * number_of_samples
        :type number_of_samples: int
        :param channel_indices: Indices of the channels to measure
        :type channel_indices: Iterable[int]
        :return: An iterable collection of the recorded measurement data
        :rtype: Iterable[PicoscopeMeasurement]
        """
