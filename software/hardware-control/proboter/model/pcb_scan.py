# Copyright (C) 2023 SCHUTZWERK GmbH
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
from tortoise import fields

from .entity import Entity
from .fields import NumpyArrayStringField, NumpyArrayUInt8Field, NumpyArrayFloat32Field


class PcbScanStatus(str, Enum):
    """
    Status of a PCB image scan
    """
    UNKNOWN = "UNKNOWN"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    CANCELLED = "CANCELLED"


class PcbScan(Entity):
    """
    Complete PCB scan

    Each scan consists of at least one PcbScanImage
    """
    # pylint: disable=too-few-public-methods
    id: int = fields.IntField(pk=True)
    # Whether the scan is visible
    is_visible: bool = fields.BooleanField(null=False, default=True)
    # User-defined name of the scan
    name: str = fields.CharField(100, null=False)
    # Lower boundary in X direction of the scan area
    x_min: float = fields.FloatField(null=False)
    # Upper boundary in X direction of the scan area
    x_max: float = fields.FloatField(null=False)
    # Lower boundary in Y direction of the scan area
    y_min: float = fields.FloatField(null=False)
    # Upper boundary in Y direction of the scan area
    y_max: float = fields.FloatField(null=False)
    # Offset in Z direction in mm from the reference XY plane
    z_offset: float = fields.FloatField(null=False, default=0.0)
    # Status of the PCB scan
    status: PcbScanStatus = fields.CharEnumField(PcbScanStatus,
                                                 null=False,
                                                 default=PcbScanStatus.UNKNOWN)
    # The raw image data
    preview_image_data: bytes = NumpyArrayUInt8Field(null=False)
    # The image width in pixel
    preview_image_width: int = fields.IntField(null=False)
    # The image height in pixel
    preview_image_height: int = fields.IntField(null=False)
    # The number of color channels
    preview_image_channels: int = fields.IntField(null=False, default=3)
    # Scan images
    images: fields.ReverseRelation["PcbScanImage"]


class PcbScanImage(Entity):
    """
    Single (partial) PCB image
    """
    # pylint: disable=too-few-public-methods
    id: int = fields.IntField(pk=True)
    # The raw image data
    image_data: bytes = NumpyArrayUInt8Field(null=False)
    # The image width in pixel
    image_width: int = fields.IntField(null=False)
    # The image height in pixel
    image_height: int = fields.IntField(null=False)
    # The number of color channels
    image_channels: int = fields.IntField(null=False, default=3)
    # Camera matrix containing the instrinsic parameters of the camera
    # system that created the image as (3x3) numpy array
    camera_matrix: np.ndarray = NumpyArrayStringField(null=True)
    # The transformation matrix of the camera system at the time of the image
    # capture as (4x4) numpy array
    tmat: np.ndarray = NumpyArrayStringField(null=True)
    # Image depth map
    depth_map: np.ndarray = NumpyArrayFloat32Field(null=True)
    # Offset in Z direction in mm from the reference XY plane
    z_offset: float = fields.FloatField(null=False, default=0.0)
    # ID of the scan the image belongs to
    # The scan the image belongs to (object reference)
    scan: fields.ForeignKeyRelation[PcbScan] = fields.ForeignKeyField("models.PcbScan",
                                                                      related_name="images",
                                                                      cascade=fields.CASCADE)
