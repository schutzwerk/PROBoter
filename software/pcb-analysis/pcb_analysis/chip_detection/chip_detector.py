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

from typing import Iterable
from abc import ABC, abstractmethod

import numpy as np

from pcb_analysis.model import Chip


class ChipDetector(ABC):
    """
    Abstract interface for a chip detector

    The detector gets an image of a PCB as input and
    returns a list of bounding boxes of detected chips.
    """

    @abstractmethod
    def detect_chips(self, image: np.ndarray) -> Iterable[Chip]:
        """
        Searches for chips in a given PCB image.

        :param image: The PCB image as numpy array. The image must
                      be a color image with 3 channels in BGR format!
        :return: An iterable collection of the detected chips.
        """

    def release(self) -> None:
        """
        Free all allocated resources
        """
