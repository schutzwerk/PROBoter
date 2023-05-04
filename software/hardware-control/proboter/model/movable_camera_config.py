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
from .axes_controller_config import AxesControllerConfig


# Longer lines allowed for readability
# pylint: disable=line-too-long
class MovableCameraConfig(CameraConfig):
    """
    Configuration for a movable camera (system)
    """
    # pylint: disable=too-few-public-methods
    # The (4x4) transformation matrix defining the camera rotation
    tmat_camera_rotation: np.ndarray = NumpyArrayStringField(null=False,
                                                             default=np.eye(4))
    # The (4x4) transformation matrix from the reference system to local
    # system of the probe that carries the camera
    tmat_ref_to_probe: np.array = NumpyArrayStringField(null=False,
                                                        default=np.eye(4))
    # The corresponding axes controller
    axes_controller: fields.OneToOneRelation["AxesControllerConfig"] = fields.OneToOneField("models.AxesControllerConfig",
                                                                                            null=False)
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.ForeignKeyRelation["ProboterConfig"] = fields.ForeignKeyField("models.ProboterConfig",
                                                                                   related_name="movable_cameras",
                                                                                   null=False)
