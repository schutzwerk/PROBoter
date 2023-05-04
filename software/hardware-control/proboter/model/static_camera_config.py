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

from .camera_config import CameraConfig
from .fields import NumpyArrayStringField


# Longer lines allowed for readability
# pylint: disable=line-too-long
class StaticCameraConfig(CameraConfig):
    """
    Configuration for a static camera (system)
    """
    # The (4x4) transformation matrix from camera system to
    # the global system
    tmat_to_global: np.ndarray = NumpyArrayStringField(null=False,
                                                       default=np.eye(4))
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.ForeignKeyRelation["ProboterConfig"] = fields.ForeignKeyField("models.ProboterConfig",
                                                                                   related_name="static_cameras",
                                                                                   null=False)
