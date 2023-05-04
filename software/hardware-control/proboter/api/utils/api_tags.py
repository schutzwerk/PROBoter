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


class ApiTags(str, Enum):
    """
    Tags used to group API endpoints
    """
    LIGHT_CONTROLLER = "light"
    SIGNAL_MULTIPLEXER = "signal-multiplexer"
    UART_INTERFACE = "uart-interface"
    TARGET_POWER_CONTROLLER = "power-controller"
    PROBOTER = "proboter"
    PROBE = "probe"
    PROBING = "probing"
    REFERENCE_BOARD = "reference-board"
    CAMERA_STATIC = "camera-static"
    TASKS = "tasks"
    DEMO_MODE = "demo-mode"
