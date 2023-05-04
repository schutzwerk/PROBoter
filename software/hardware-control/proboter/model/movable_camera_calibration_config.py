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
from .movable_camera_config import MovableCameraConfig
from .camera_calibration_config import CameraCalibrationConfig


# Longer lines allowed for readability
# pylint: disable=line-too-long
class MovableCameraCalibrationConfig(CameraCalibrationConfig):
    """
    Calibration related settings of a movable camera system
    """
    # Camera delay in seconds after each camera movement
    # (used to stabilize the illumination and white balancing)
    camera_delay: float = fields.FloatField(null=False, default=4.0)
    # Calibration feed in mm/min
    calibration_feed: float = fields.FloatField(null=False, default=10000)
    # Whether the camera should be homed before a calibration run
    home_before_calibration: bool = fields.BooleanField(null=False,
                                                        default=True)
    # Positions where four the reference board QR code-like markers are visible
    # as (4x2) matrix
    initial_positions: np.ndarray = NumpyArrayStringField(null=False,
                                                          default=np.zeros((4, 2)))
    # The camera config the calibration belongs to
    camera: fields.OneToOneRelation["MovableCameraConfig"] = fields.OneToOneField("models.MovableCameraConfig",
                                                                                  related_name="calibration_config",
                                                                                  on_delete=fields.CASCADE)
