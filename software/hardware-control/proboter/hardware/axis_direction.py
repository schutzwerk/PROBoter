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


class AxisDirection(str, Enum):
    """
    Possible moving axis directions
    """
    X = "X"
    Y = "Y"
    Z = "Z"

    @staticmethod
    def to_index(axis_direction: "AxisDirection") -> int:
        """
        Return the numeric index of a given axis direction

        X -> 0
        Y -> 1
        Z -> 2

        :param axis_direction: Axis direction
        :type axis_direction: AxisDirection
        :return: Numeric index of the axis direction
        :rtype: int
        """
        return sorted(list(AxisDirection)).index(axis_direction)
