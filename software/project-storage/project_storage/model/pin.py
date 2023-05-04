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

from .pcb import Pcb
from .electrical_net import ElectricalNet
from .pcb_component import PcbComponent
from .database import db, NumpyArrayStringType


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class Pin(db.Model):
    """
    A PCB component pin or test pad
    """
    __allow_unmapped__ = True

    # Unique identifier of the pin
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # Whether the pin is visible or not
    is_visible: Mapped[bool] = db.Column(db.Boolean,
                                         nullable=False,
                                         default=True)
    # Whether the pin is temporary / not yet commited by the user
    is_temporary: Mapped[bool] = db.Column(db.Boolean,
                                           nullable=False,
                                           default=False)
    # User-defined name of the network
    name: Mapped[str] = db.Column(db.String(100),
                                  nullable=True)
    # Coordinates of the center of the pin as 3D vector
    center: Mapped[np.array] = db.Column(NumpyArrayStringType,
                                         nullable=False,
                                         default=np.empty((0, 3)))
    # Contour of the pin as (nx2) numpy array (optional)
    contour: Mapped[np.array] = db.Column(NumpyArrayStringType,
                                          nullable=True,
                                          default=None)
    # ID of the PCB the pin belongs to
    pcb_id: Mapped[int] = db.Column(db.Integer,
                                    db.ForeignKey(Pcb.id),
                                    nullable=True)
    # The PCB the pin belongs to (object reference)
    pcb: Mapped[Pcb] = db.relationship(Pcb,
                                       backref=db.backref('pins',
                                                          lazy=True,
                                                          cascade='all, delete-orphan'))
    # ID of the network the pin belongs to
    network_id: Mapped[int] = db.Column(db.Integer,
                                        db.ForeignKey(ElectricalNet.id),
                                        nullable=True)
    # The network this pin belongs to (object reference)
    network: Mapped[ElectricalNet] = db.relationship(ElectricalNet,
                                                     backref=db.backref('pins',
                                                                        lazy=True))

    # ID of the component the pin belongs to
    component_id: Mapped[int] = db.Column(db.Integer,
                                          db.ForeignKey(PcbComponent.id),
                                          nullable=True)
    # The component the pin belongs to (object reference)
    component: Mapped[PcbComponent] = db.relationship(PcbComponent,
                                                      backref=db.backref('pins',
                                                                         lazy=True,
                                                                         cascade=('all, '
                                                                                  'delete-orphan')))
