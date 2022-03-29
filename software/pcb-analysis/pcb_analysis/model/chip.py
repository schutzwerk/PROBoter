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

import uuid
from enum import Enum
from typing import Iterable
from dataclasses import dataclass, field

import numpy as np

from .pin import Pin


class ChipType(str, Enum):
    """
    Detectable chip / IC types
    """
    UNKNOWN = 'UNKNOWN'
    IC = 'IC'
    CONNECTOR_SMD = 'CONN_SMD'
    CONNECTOR_THT = 'CONN_THT'
    IC_UNPOPULATED = 'IC_UNPOP'


class ChipPackage(str, Enum):
    """
    Detectable chip packages
    """
    UNKNOWN = 'UNKNOWN'
    SON = 'SON'
    SOP = 'SOP'
    QFN = 'QFN'
    QFP = 'QFP'
    BGA = 'BGA'
    THT = 'THT'


class ChipBorderRegion(int, Enum):
    """
    Chip border regions
    """
    LEFT = 0
    RIGHT = 1
    TOP = 2
    BOTTOM = 3


@dataclass
class Chip:
    """
    An integrated circuit (IC) or chip detection
    """
    # The chip unique identifier
    chip_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # The chip package
    package: ChipPackage = ChipPackage.UNKNOWN
    # Chip vendor
    vendor: str = None
    # Chip marking
    marking: str = None
    # Confidence of the detection in the range of [0, 1.0]
    confidence: float = 0.0
    # The chip bounding box (currently a rectangular
    # bounding box defined by 4 vertices)
    bbox: np.ndarray = np.empty((4, 2))
    # Private field required for bbox type checking
    _bbox: int = field(init=False, repr=False)
    # List of pins belonging to the chip
    pins: Iterable[Pin] = ()

    @property
    # pylint: disable=function-redefined
    def bbox(self) -> np.ndarray:
        """
        The chip's bounding box defined as list of 2D vertices
        """
        return self._bbox

    @bbox.setter
    def bbox(self, bbox: np.ndarray):
        if not isinstance(bbox, np.ndarray):
            raise ValueError("bbox must a numpy array")
        if len(bbox.shape) != 2:
            raise ValueError("bbox must be a 2D array")
        if bbox.shape[1] != 2:
            raise ValueError("bbox dim 1 must be 2 (2D points)")
        self._bbox = bbox
