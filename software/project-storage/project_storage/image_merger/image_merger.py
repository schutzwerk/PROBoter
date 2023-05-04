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

from abc import ABC, abstractmethod

import numpy as np

from project_storage.model import PcbScan


class ImageMergeException(Exception):
    """
    Base class for all image merger related exceptions
    """


class ImageMerger(ABC):
    """
    An interface for algorithms that merge multiple PCB images
    into a single combined image
    """

    @abstractmethod
    def merge_scan(self, scan: PcbScan, resolution: float,
                   default_background=(128, 128, 128)) -> np.ndarray:
        """
        Generate a merged image bases on multiple PCB scan images

        The size of the final image is calculated as follows:
        width = <scan range in x> / resolution
        height = <scan range in y> / resolution

        @param scan: The PCB scan to merge
        @param resolution: The resolution of the final image in
                           millimeters per pixel
        @param default_background: The default background color as
                                   tuple of RGB values in the range
                                   of [0, 255] (uint values)
        """

    def release(self):
        """
        Release all reserved resources
        """
