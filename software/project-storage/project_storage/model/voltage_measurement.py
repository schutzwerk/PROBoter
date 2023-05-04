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

from .pin import Pin
from .database import db, NumpyArrayStringType


# pylint: disable=too-few-public-methods
class VoltageMeasurement(db.Model):
    """
    A voltage measurement at a single pin
    """
    __allow_unmapped__ = True

    # Unique identifier of the measurement
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # User-defined description of the measurement
    description: Mapped[str] = db.Column(db.String(200),
                                         nullable=True)
    # The measurements of this measurment cycle as an array
    measurements: Mapped[np.ndarray] = db.Column(NumpyArrayStringType,
                                                 nullable=False)
    # The time resolution of the measurement in ns
    time_resolution_in_ns: Mapped[float] = db.Column(db.Float,
                                                     nullable=False)
    # ID of the pin this measurement corresponds to
    pin_id: Mapped[int] = db.Column(db.Integer,
                                    db.ForeignKey(Pin.id),
                                    nullable=True)
    # The pin the measurement belongs to (object reference)
    pin: Mapped[Pin] = db.relationship(Pin,
                                       backref=db.backref('measurements',
                                                          lazy=True,
                                                          cascade="all, delete-orphan"))
