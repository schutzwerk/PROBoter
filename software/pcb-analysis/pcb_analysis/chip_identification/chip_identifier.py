# Copyright (C) 2022 SCHUTZWERK GmbH
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
from abc import ABC, abstractmethod

import numpy as np


class ChipIdentifier(ABC):
    """
    Base class for pin identifiers
    """

    logger = logging.getLogger(__module__)

    @abstractmethod
    def read_chip_id(self, chip_image: np.ndarray) -> str:
        """
        Reads the chip marking / ID from the chip housing

        :param chip_image: Image of the chip housing
        :type chip_image: np.ndarray
        :return: A string containing the chip marking / ID
        :rtype: str
        """

    def release(self) -> None:
        """
        Free all allocated resources
        """
