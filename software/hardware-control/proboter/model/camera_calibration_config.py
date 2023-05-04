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

from tortoise import fields

from .entity import Entity


class CameraCalibrationConfig(Entity):
    """
    Base class for all camera calibration configs
    """
    # pylint: disable=too-few-public-methods
    # Unique identifier of the camera calibration settings
    id: int = fields.IntField(pk=True)
    # Threshold of the mean brightness value used to determine the thresholding
    # algorithm used for image binarization in the range [0,255]
    brightness_threshold: int = fields.IntField(null=False, default=150)
