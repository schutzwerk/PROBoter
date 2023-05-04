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

from sqlalchemy.orm import Mapped

from .pcb import Pcb
from .database import db


# pylint: disable=too-few-public-methods
class ElectricalNet(db.Model):
    """
    An electrical net consisting of multiple pins
    """
    __allow_unmapped__ = True

    # Unique identifier of the network instance
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # Whether the network is visible or not
    is_visible: Mapped[bool] = db.Column(db.Boolean,
                                         nullable=False,
                                         default=True)
    # Whether the network is temporary / not yet commited by the user
    is_temporary: Mapped[bool] = db.Column(db.Boolean,
                                           nullable=False,
                                           default=False)
    # User-defined name of the network
    name: Mapped[str] = db.Column(db.String(100),
                                  nullable=True)
    # ID of the PCB the network belongs to
    pcb_id: Mapped[int] = db.Column(db.Integer,
                                    db.ForeignKey(Pcb.id),
                                    nullable=True)
    # The PCB the network belongs to (object reference)
    pcb: Mapped[Pcb] = db.relationship(Pcb,
                                       backref=db.backref('networks',
                                                          lazy=True,
                                                          cascade="all, delete-orphan"))
