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

from datetime import datetime

import numpy as np
from sqlalchemy.orm import Mapped

from .pcb import Pcb
from .database import db, NumpyArrayStringType, NumpyArrayUInt8Type


# pylint: disable=too-few-public-methods
class PcbScan(db.Model):
    """
    Complete PCB scan

    Each scan consists of at least one PcbScanImage
    """
    __allow_unmapped__ = True

    # Unique identifier of the scan
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # Whether the scan is visible
    is_visible: Mapped[bool] = db.Column(db.Boolean,
                                         nullable=False,
                                         default=True)
    # User-defined name of the scan
    name: Mapped[str] = db.Column(db.String(100),
                                  nullable=False)
    # Date when the scan was created
    created: Mapped[datetime] = db.Column(db.DateTime,
                                          default=datetime.utcnow,
                                          nullable=False)
    # Lower boundary in X direction of the scan area
    x_min: Mapped[float] = db.Column(db.Float,
                                     nullable=False)
    # Upper boundary in X direction of the scan area
    x_max: Mapped[float] = db.Column(db.Float,
                                     nullable=False)
    # Lower boundary in Y direction of the scan area
    y_min: Mapped[float] = db.Column(db.Float,
                                     nullable=False)
    # Upper boundary in Y direction of the scan area
    y_max: Mapped[float] = db.Column(db.Float,
                                     nullable=False)
    # Offset in Z direction in mm from the reference XY plane
    z_offset: Mapped[float] = db.Column(db.Float,
                                        nullable=False,
                                        default=0.0)
    # ID of the PCB the scan belongs to
    pcb_id: Mapped[int] = db.Column(db.Integer,
                                    db.ForeignKey(Pcb.id),
                                    nullable=True)
    # The PCB the scan belongs to (object reference)
    pcb: Mapped[Pcb] = db.relationship(Pcb,
                                       backref=db.backref('scans',
                                                          lazy=True,
                                                          cascade='all, delete-orphan'))
    # The raw image data
    preview_image_data: Mapped[np.ndarray] = db.deferred(db.Column(NumpyArrayUInt8Type,
                                                                   nullable=False))
    # The image width in pixel
    preview_image_width: Mapped[int] = db.Column(db.Integer,
                                                 nullable=False)
    # The image height in pixel
    preview_image_height: Mapped[int] = db.Column(db.Integer,
                                                  nullable=False)
    # The number of color channels
    preview_image_channels: Mapped[int] = db.Column(db.Integer,
                                                    nullable=False,
                                                    default=3)

    @property
    def width(self) -> float:
        """
        Scan width == dimension in X direction
        """
        return self.x_max - self.x_min

    @property
    def height(self) -> float:
        """
        Scan height == dimension in Y direction
        """
        return self.y_max - self.y_min


# pylint: disable=too-few-public-methods
class PcbScanImage(db.Model):
    """
    Single (partial) PCB image
    """
    __allow_unmapped__ = True

    # Unique identifier of the image
    id: Mapped[int] = db.Column(db.Integer,
                                primary_key=True)
    # Date when the scan was created
    created: Mapped[datetime] = db.Column(db.DateTime,
                                          default=datetime.utcnow,
                                          nullable=False)
    # The raw image data
    image_data: Mapped[bytes] = db.deferred(db.Column(NumpyArrayUInt8Type,
                                                      nullable=False))
    # The image width in pixel
    image_width: Mapped[int] = db.Column(db.Integer,
                                         nullable=False)
    # The image height in pixel
    image_height: Mapped[int] = db.Column(db.Integer,
                                          nullable=False)
    # The number of color channels
    image_channels: Mapped[int] = db.Column(db.Integer,
                                            nullable=False,
                                            default=3)
    # Camera matrix containing the instrinsic parameters of the camera
    # system that created the image as (3x3) numpy array
    camera_matrix: Mapped[np.ndarray] = db.Column(NumpyArrayStringType,
                                                  nullable=True)
    # The transformation matrix of the camera system at the time of the image
    # capture as (4x4) numpy array
    tmat: Mapped[np.ndarray] = db.Column(NumpyArrayStringType,
                                         nullable=False)
    # Offset in Z direction in mm from the reference XY plane
    z_offset: Mapped[float] = db.Column(db.Float,
                                        nullable=False,
                                        default=0.0)
    # ID of the scan the image belongs to
    scan_id: Mapped[int] = db.Column(db.Integer,
                                     db.ForeignKey(PcbScan.id),
                                     nullable=False)
    # The scan the image belongs to (object reference)
    scan: Mapped[PcbScan] = db.relationship(PcbScan,
                                            backref=db.backref('images',
                                                               lazy=True,
                                                               cascade='all, delete-orphan'))
