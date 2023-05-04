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

from .fields import NumpyArrayStringField
from .static_camera_config import StaticCameraConfig
from .camera_calibration_config import CameraCalibrationConfig


# Longer lines allowed for readability
# pylint: disable=line-too-long
class StaticCameraCalibrationConfig(CameraCalibrationConfig):
    """
    Calibration related settings of a static camera system
    """
    # Snapshot image resolution
    image_resolution: np.array = NumpyArrayStringField(null=False,
                                                       default=np.array([1920, 1080]))
    # The camera config the calibration belongs to
    camera: fields.OneToOneRelation["StaticCameraConfig"] = fields.OneToOneField("models.StaticCameraConfig",
                                                                                 related_name="calibration_config",
                                                                                 on_delete=fields.CASCADE)
