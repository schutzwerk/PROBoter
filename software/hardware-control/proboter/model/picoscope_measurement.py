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
from .fields import NumpyArrayFloat32Field


class PicoscopeTriggerSource(str, Enum):
    """
    Voltage signal measurement trigger source
    """
    TARGET_POWER_LINE = 'TARGET_POWER_LINE'
    ANALOG_INPUT = 'ANALOG_INPUT'


class PicoscopeMeasurement(Entity):
    """
    A single picoscope measurement cycle
    """
    # pylint: disable=too-few-public-methods
    # Unique identifier of the measurement
    id: int = fields.IntField(pk=True)
    # Trigger used for the measurement
    trigger: PicoscopeTriggerSource = fields.CharEnumField(
        PicoscopeTriggerSource,
        null=False,
        default=PicoscopeTriggerSource.TARGET_POWER_LINE)
    # User-defined description of the PCB
    description: str = fields.CharField(200, null=False)
    # The measurements of this measurment cycle as an array
    measurements: np.ndarray = NumpyArrayFloat32Field(null=False)
    # The time resolution of the measurement in ns
    time_resolution_in_ns: float = fields.FloatField(null=False)
    # Index of the pin this measurement corresponds to
    pin_index: int = fields.IntField(null=False)
