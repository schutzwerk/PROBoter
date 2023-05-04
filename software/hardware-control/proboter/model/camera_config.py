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

import numpy as np
from tortoise import fields


from .entity import Entity
from .fields import NumpyArrayStringField


class CameraConfig(Entity):
    """
    Configuration of a generic camera system
    """
    # pylint: disable=too-few-public-methods
    # The camera ID
    id: int = fields.IntField(pk=True)
    # The name of the camera (system)
    name: str = fields.CharField(100, null=False)
    # USB device to use
    usb_device_name: str = fields.CharField(100, null=True)
    # The camera resolution in pixel (width)
    resolution_width: int = fields.IntField(null=False)
    # The camera resolution in pixel (height)
    resolution_height: int = fields.IntField(null=False)
    # Framerate in FPS
    framerate: int = fields.IntField(null=False, default=25)
    # The (3x3) camera calibration matrix
    camera_matrix: np.array = NumpyArrayStringField(null=False,
                                                    default=np.eye(3))
    # Distortion coefficients as (1x5) matrix
    distortion_coefficients: np.array = NumpyArrayStringField(null=False,
                                                              default=np.zeros((1, 5)))
