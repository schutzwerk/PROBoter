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


# Longer lines allowed for readability
# pylint: disable=line-too-long
class PicoscopeConfig(Entity):
    """
    Picoscope (oscilloscope) configuration

    For more information about this PC oscilloscope see:
    https://www.picotech.com/products/oscilloscope
    """
    # The Picoscope ID
    id: int = fields.IntField(pk=True)
    # The device name of the picoscope
    name: str = fields.CharField(100, null=False)
    # Voltage range channel A
    voltage_range_a: int = fields.IntField(null=False,
                                           default=5000)
    # Voltage range channel B
    voltage_range_b: int = fields.IntField(null=False,
                                           default=5000)
    # Time resolution in naoseconds
    time_resolution_in_ns: int = fields.IntField(null=False,
                                                 default=25)
    # Measurement duration in microseconds
    duration_us: int = fields.IntField(null=False,
                                       default=300000)
    # Level at which measurement is automatically triggered in milli Volt
    trigger_level_mv: int = fields.IntField(null=False,
                                            default=1500)
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.OneToOneRelation["ProboterConfig"] = fields.OneToOneField("models.ProboterConfig",
                                                                               related_name="picoscope",
                                                                               null=False)
