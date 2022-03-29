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
from dataclasses import dataclass, field

import numpy as np


@dataclass
class Pin:
    """
    A chip pin detection
    """
    # The unique pin identifier
    pin_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Confidence of the detection in the range of [0, 1.0]
    confidence: float = 0.0
    # The pin center coordinate as 2D point
    center: np.ndarray = field(default_factory=lambda: np.empty((0, 2)))
    # The pin countour defined by multiple 2D points
    contour: np.ndarray = field(default_factory=lambda: np.empty((0, 2)))
