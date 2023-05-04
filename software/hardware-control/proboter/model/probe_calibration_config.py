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


# Longer lines allowed for readability
# pylint: disable=line-too-long
class ProbeCalibrationConfig(Entity):
    """
    Calibration related settings of an electrical probing unit
    """
    # pylint: disable=too-few-public-methods
    # Unique identifier of the probe calibration settings
    id: int = fields.IntField(pk=True)
    # Calibration feed in mm/min
    calibration_feed: float = fields.FloatField(null=False, default=1000)
    # Whether the probe should be homed before a calibration run
    home_before_calibration: bool = fields.BooleanField(
        null=False, default=True)
    # The 4 initial probe positions as (4x3) numpy array
    initial_probe_positions: np.ndarray = NumpyArrayStringField(null=False)
    # The probe this config belongs to
    probe: fields.OneToOneRelation["ProbeConfig"] = fields.OneToOneField("models.ProbeConfig",
                                                                         related_name="calibration_config",
                                                                         on_delete=fields.CASCADE)
