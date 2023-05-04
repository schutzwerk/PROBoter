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
from .fields import NumpyArrayStringField
from .axes_controller_config import AxesControllerConfig


class ProbeType(str, Enum):
    """
    Probe type that defines the location of the probe inside the PROBoter
    hardware platform
    """
    # The left outermost probe
    P21 = 'P21'
    # The middle left probe
    P2 = 'P2'
    # The middle right probe
    P1 = 'P1'
    # The right outermost probe
    P11 = 'P11'

    def to_order_index(self) -> int:
        """
        Return a numerical order index of the probe type

        The probe type order is as follows:
        P11 -> P1 -> P2 -> P21
        """
        if self == ProbeType.P11:
            return 0
        if self == ProbeType.P1:
            return 1
        if self == ProbeType.P2:
            return 2
        return 3


# Longer lines allowed for readability
# pylint: disable=line-too-long
class ProbeConfig(Entity):
    """
    Configuration for a single PROBoter probe
    """
    # pylint: disable=too-few-public-methods
    # The probe ID
    id: int = fields.IntField(pk=True)
    # The name of the probe
    name: str = fields.CharField(100, null=False)
    # The probe type defining the probe's location in the
    # PROBoter hardware platform
    probe_type: ProbeType = fields.CharEnumField(ProbeType, null=False)
    # The ordering index of the probe (used for collision detection)
    order_index: int = fields.IntField(null=False)
    # The 4x4 transformation matrix that describes
    # the transformation from the probe -> global
    # coordinate system
    tmat_to_glob: np.ndarray = NumpyArrayStringField(null=False,
                                                     default=np.eye(4))
    # Safety position in positive x direction of the probe as 3D vector
    # in probe-local coordinates
    pos_x_safety_position: np.ndarray = NumpyArrayStringField(null=False,
                                                              default=np.zeros(3))
    # Safety position in negative x direction of the probe as 3D vector
    # in probe-local coordinates
    neg_x_safety_position: np.ndarray = NumpyArrayStringField(null=False,
                                                              default=np.zeros(3))
    # Axes controller config
    # The corresponding probe configuration
    axes_controller: fields.OneToOneRelation["AxesControllerConfig"] = fields.OneToOneField(
        "models.AxesControllerConfig",
        on_delete=fields.CASCADE,
        related_name="probe")
    # Calibration config
    calibration_config: fields.BackwardOneToOneRelation["ProbeCalibrationConfig"]
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.ForeignKeyRelation["ProboterConfig"] = fields.ForeignKeyField("models.ProboterConfig",
                                                                                   related_name="probes",
                                                                                   null=False)
