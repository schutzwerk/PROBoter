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

from enum import Enum

import numpy as np
from sqlalchemy.orm import Mapped

from .pcb import Pcb
from .database import db, NumpyArrayStringType


class PcbComponentPackage(str, Enum):
    """
    Component package
    """
    THT = 'THT'
    SON = 'SON'
    SOP = 'SOP'
    QFN = 'QFN'
    QFP = 'QFT'
    UNKNOWN = 'UNKNOWN'


# pylint: disable=too-few-public-methods
class PcbComponent(db.Model):
    """
    An (active) component, e.g. an IC, detected on a PCB
    """
    __allow_unmapped__ = True

    # Unique identifier of the PCB component
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # Whether the component is visible or not
    is_visible: Mapped[bool] = db.Column(db.Boolean,
                                         nullable=False,
                                         default=True)
    # Whether the component is temporary / not yet commited by the user
    is_temporary: Mapped[bool] = db.Column(db.Boolean,
                                           nullable=False,
                                           default=False)
    # A displayable name of the component
    name: Mapped[str] = db.Column(db.String(100),
                                  nullable=True,
                                  default='IC')
    # The component marking / vendor ID
    marking: Mapped[str] = db.Column(db.String(100),
                                     nullable=True)
    # The component vendor name
    vendor: Mapped[str] = db.Column(db.String(100),
                                    nullable=True)
    # The component package
    package: Mapped[PcbComponentPackage] = db.Column(db.Enum(PcbComponentPackage),
                                                     nullable=False,
                                                     default=PcbComponentPackage.UNKNOWN)
    # Component contour as (nx3) numpy array. The contour is described by
    # n vertices forming a 3D polygon.
    contour: Mapped[np.ndarray] = db.Column(NumpyArrayStringType,
                                            nullable=False,
                                            default=np.empty((0, 3)))
    # ID of the PCB the component belongs to
    pcb_id: Mapped[int] = db.Column(db.Integer,
                                    db.ForeignKey(Pcb.id),
                                    nullable=True)
    # The PCB the component belongs to (object reference)
    pcb: Mapped[Pcb] = db.relationship(Pcb,
                                       backref=db.backref('components',
                                                          lazy=True,
                                                          cascade='all, delete-orphan'))
