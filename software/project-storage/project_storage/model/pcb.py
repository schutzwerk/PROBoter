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

import numpy as np
from sqlalchemy.orm import Mapped

from .database import db, NumpyArrayUInt8Type


# pylint: disable=too-few-public-methods
class Pcb(db.Model):
    """
    A revere-engineered / assessed PCB (Printed Circuit Board)
    """
    # Unique identifier of the PCB
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # User-defined name of the PCB
    name: Mapped[str] = db.Column(db.String(100),
                                  nullable=True)
    # User-defined description of the PCB
    description: Mapped[str] = db.Column(db.String(200),
                                         nullable=True)
    # PCB thickness in mm
    thickness: Mapped[float] = db.Column(db.Float(2.0),
                                         nullable=False)
    # Preview image data of a stitched pcb scan
    preview_image_data: Mapped[np.ndarray] = db.deferred(db.Column(NumpyArrayUInt8Type,
                                                                   nullable=True))
    # The image width in pixel
    preview_image_width: Mapped[int] = db.Column(db.Integer,
                                                 nullable=True)
    # The image height in pixel
    preview_image_height: Mapped[int] = db.Column(db.Integer,
                                                  nullable=True)
