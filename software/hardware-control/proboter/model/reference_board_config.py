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


class ReferenceBoardConfig(Entity):
    """
    Reference board configuration used for the calibration
    of the PROBoter hardware
    """
    # pylint: disable=too-few-public-methods
    # The unique board config identifier
    id: int = fields.IntField(pk=True)
    # Name of the configuration board
    name: str = fields.CharField(100, null=False)
    # Width of the reference pattern in mm
    inner_brass_pin_width: float = fields.FloatField(null=False)
    # Height of the reference pattern in mm
    inner_brass_pin_height: float = fields.FloatField(null=False)
    # Width of the outer 4 pins of the reference pattern in mm
    raised_brass_pin_width: float = fields.FloatField(null=False)
    # Height of the outer 4 pins of the reference pattern in mm
    raised_brass_pin_height: float = fields.FloatField(null=False)
    # Reference board thickness in mm
    thickness: float = fields.FloatField(null=False)
    # Reference marker width in mm
    marker_width: float = fields.FloatField(null=False)
    # Reference marker height in mm
    marker_height: float = fields.FloatField(null=False)
    # Width of the reference marker grid in mm
    marker_grid_width: float = fields.FloatField(null=False)
    # Height of the reference marker grid in mm
    marker_grid_height: float = fields.FloatField(null=False)
    # Width of the 4 outer white reference pin set in mm
    outer_white_pin_width: float = fields.FloatField(null=False)
    # Height of the 4 outer white reference pin set in mm
    outer_white_pin_height: float = fields.FloatField(null=False)
    # Width of the 4 outer brass reference pin set in mm
    outer_brass_pin_width: float = fields.FloatField(null=False)
    # Height of the 4 outer brass reference pin set in mm
    outer_brass_pin_height: float = fields.FloatField(null=False)
