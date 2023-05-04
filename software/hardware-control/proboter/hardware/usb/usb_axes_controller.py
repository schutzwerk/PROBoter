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

import re
import os
import json
import logging
from asyncio import Lock
from typing import Iterable, Optional

import numpy as np

from proboter.model import AxesControllerConfig
from proboter.hardware import AxesControllerConnectionException, \
    AxesControllerException, AxisDirection

from .utils import send_uart_command


class UsbAxesController:
    """
    Low level control that handles the communication with
    a 5-axis control board (SKR v1.3) running a modified Marlin
    firmware
    """

    # Light controller value range
    MIN_LIGHT_INTENSITY = 0
    MAX_LIGHT_INTENSITY = 255

    # G-Code patterns used to communicate with
    # the control board running Marlin
    G_CODE_ABS_POSITIONING = "G90"
    G_CODE_REL_POSITIONING = "G91"
    G_CODE_RAPID_LINEAR_MOVEMENT = "G0 {pos:s} F{feed:f}"
    G_CODE_SET_MAX_AXIS_FEED = "M203 {axis:s}{feed:f}"
    G_CODE_SET_AXIS_ACCELERATION = "M201 {axis:s}{acc:f}"
    G_CODE_SET_LIGHT_INTENSITY = "M376 I{intensity:}"
    G_CODE_PROBE_REFERENCE_PIN = "M370"

    COMMAND_DELIMITER = "\n"
    RESPONSE_DELIMITER = "\n"
    RESPONSE_PATTERN_OK = r"(.*\n)*ok\n$"
    RESPONSE_PATTERN_ERROR = r"(.*\n)*Error:(.*)"

    # Global lock to access the access controller board peripherals
    SERIAL_LOCK = Lock()
    # Global map of all identified access controller boards
    # Each entry consists of a tuple <USB device> : <UUID>
    USB_DEVICE_UUID_MAP = {}

    log = logging.getLogger(__module__)

    def __init__(self, config: AxesControllerConfig):
        self._config = config

        self._usb_device = None
        self._command_lock = Lock()

    @property
    def is_connected(self) -> bool:
        """
        Whether the hardware unit is connected

        :rtype: bool
        """
        return self._usb_device is not None

    @property
    def is_light_controller(self) -> bool:
        """
        Return whether the axes controller is configured to be
        the light controller
        """
        return self._config.is_light_controller

    async def start(self):
        """
        Set up the connection to the axes controller board
        """
        # Stop all previously registered USB monitors
        await self.stop()

        # Check if device exists
        if not os.path.exists(self._config.usb_device_name):
            self.log.warning("Configured axes controller device not found")
            self._usb_device = None
        else:
            self.log.info("Using axes controller device %s",
                          self._config.usb_device_name)
            self._usb_device = self._config.usb_device_name

    async def stop(self) -> None:
        """
        Shutdown the axes controller board
        """
        self._usb_device = None

    async def read_uuid(self) -> Optional[str]:
        """
        Read the device-specific UUID from a controller board

        :param usb_device: Name / path of the USB TTY device to query
        :type usb_device: str
        :param baud_rate: The UART baudrate of the controller board
        :type baud_rate: int
        :return: The UUID of the controller board
        :rtype: str
        """
        # Send an UUID request to the controller board
        uuid_response = await self._send_controller_board_command("M115",
                                                                  self._usb_device,
                                                                  self._config.baud_rate,
                                                                  timeout=2)
        # Extract the UUID
        matcher_uuid = re.compile(r".*UUID:(?P<uuid>\w{8}-\w{4}-\w{4}-\w{4}-\w{12}).*",
                                  re.DOTALL)
        match_res = matcher_uuid.match(uuid_response)
        if match_res:
            self.log.debug("UUID response: %s", match_res.group("uuid"))
            return match_res.group("uuid")
        self.log.warning("Failed to read UUID")
        return None

    async def home(self, axes: Iterable[AxisDirection] = None):
        """
        Home all axes
        """
        if axes is None:
            await self._send_command("G28 Z")
            await self._send_command("G28 X Y")
        else:
            for axis in axes:
                if axis not in AxisDirection:
                    raise ValueError(
                        f"Invalid axis specifier '{axis}'")
            await self._send_command(f"G28 {' '.join(axes)}")

    async def move_to_position(self, position: np.ndarray, feed: float = 300,
                               raise_z: bool = False) -> None:
        """
        Move the unit to a given absolute position.


        :param position: The position in the local axes controller system
                         as (1x3) numpy array containing the [x, y, z]
                         coordinates
        :type position: np.ndarray
        :param feed: The feed rate for all axes in mm/min
        :type feed: float
        :param raise_z: Whether to raise the z axis before a movement in the
                        XY plane
        :type raise_z: bool
        """
        # Ensure absolute positioning
        await self._send_command(self.G_CODE_ABS_POSITIONING)

        # Get current position
        cur_position = await self.get_position()

        if raise_z and (position[0] != cur_position[0]
                        or position[1] != cur_position[1]):
            # Raise in z-axis
            position_string = self._format_position(cur_position[0],
                                                    position[1],
                                                    0)
            move_command = self.G_CODE_RAPID_LINEAR_MOVEMENT.format(pos=position_string,
                                                                    feed=feed)
            await self._send_command(move_command)

            # Move to x, y coordinates
            position_string = self._format_position(position[0],
                                                    position[1],
                                                    0)
            move_command = self.G_CODE_RAPID_LINEAR_MOVEMENT.format(pos=position_string,
                                                                    feed=feed)
            await self._send_command(move_command)

        # Lower z-axis to final position
        position_string = self._format_position(position[0],
                                                position[1],
                                                position[2])
        move_command = self.G_CODE_RAPID_LINEAR_MOVEMENT.format(pos=position_string,
                                                                feed=feed)
        await self._send_command(move_command)
        # This call is required for blocking until the commands has finished
        await self.get_position()

    async def get_position(self) -> np.ndarray:
        """
        Reads the current units x, y and z position.

        :return: A (1x3) numpy array containing the [x, y, z] coordinates of
                 the controller board
        :rtype: np.ndarray
        """
        response = await self._send_command("M114")

        # Setup the pattern to retrieve the axes position
        pattern = r"(.*\n)*X:(?P<x>-?[0-9]+\.[0-9]+)\s+"
        pattern += r"Y:(?P<y>-?[0-9]+\.[0-9]+)\s+"
        pattern += r"Z:(?P<z>-?[0-9]+\.[0-9]+).*"
        matcher = re.compile(pattern, re.MULTILINE)

        match = matcher.match(response)
        if not match:
            raise AxesControllerException(
                f"Axes position not parsable. Response was {response}")

        return np.array([float(match.group('x')),
                         float(match.group('y')),
                         float(match.group('z'))])

    async def enable_motors(self) -> None:
        """
        Enables power on all axes
        """
        await self._send_command("M17")

    async def disable_motors(self) -> None:
        """
        Disables power on all axes
        """
        await self._send_command("M18 X Y Z")

    async def set_axis_max_feed(self, axis: AxisDirection, max_feed: int) -> None:
        """
        Sets the max. feed rate for a single axis.

        The given value overrides any firmware defaults!

        :param axis: The axis to configure. One of 'X', 'Y' or 'Z'
        :type axis: AxisDirection
        :param max_feed: The max. feed rate in mm/min
        :type max_feed: int
        """
        cmd = self.G_CODE_SET_MAX_AXIS_FEED.format(axis=axis, feed=max_feed)
        await self._send_command(cmd)

    async def set_axis_acceleration(self, axis: AxisDirection,
                                    acceleration: int) -> None:
        """
        Sets the acceleration used for accelerated movements for a single
        aix.

        The given value overrides any firmware defaults!

        :param axis: The axis to configure. One of 'X', 'Y' or 'Z'
        :type axis: AxisDirection
        :param acceleration: The axis acceleration in mm/sec^2
        :type acceleration: int
        """

        cmd = self.G_CODE_SET_AXIS_ACCELERATION.format(axis=axis,
                                                       acc=acceleration)
        await self._send_command(cmd)

    async def emergency_stop(self) -> None:
        """
        Emergency stopping the unit.

        A reset of the unit is required to
        return to operational mode!
        """
        await self._send_command("M112")

    async def get_driver_status(self) -> str:
        """
        Reports the status of the stepper motor drivers
        (TMC drivers only!)

        :return: A string containing information about the
                 stepper driver status.
        :rtype: str
        """
        return await self._send_command("M122")

    async def get_endstop_states(self) -> str:
        """
        Reports the current state of all endstops.
        :return: A string containing information about the
                 current endstop states.
        :rtype: str
        """
        return await self._send_command("M119")

    async def center_probe(self) -> np.ndarray:
        """
        Runs a 4-point incremental probe centering cycle.
        Before running this, the probe must be positioned so
        that it touches the reference pin when lowering the
        z axis. If not, the probe can be damaged or destroyed!!

        :return: A numpy array of dimensions (4x3) with the
                 coordinates of the reference pin edge
        :rtype: np.ndarray
        """
        # Trigger the probing routine
        raw_output = await self._send_command(self.G_CODE_PROBE_REFERENCE_PIN)

        # Extract the points from the raw output
        pattern = re.compile(
            r"calibration_points:\s?(?P<coords>.*)ok", re.DOTALL)
        match = pattern.findall(raw_output)
        if not match:
            raise AxesControllerException(
                "No calibration point coordinates sent")

        coords_string = match[0].strip()
        try:
            coords_json = json.loads(match[0])
        except json.JSONDecodeError as exc:
            raise AxesControllerException(
                "Invalid calibration point format", exc) from None

        if len(coords_json) != 4:
            raise AxesControllerException(("Invalid number of calibration points:"
                                           f" {len(coords_json):d} must be 4"))

        # Format check
        for i in range(4):
            if 'x' not in coords_json[i] \
               or 'y' not in coords_json[i] \
               or 'z' not in coords_json[i]:
                raise AxesControllerException(
                    f"Invalid coordinate data format: {coords_string}")

        # Convert the coordinates
        coords = np.zeros((4, 3))
        try:
            for i in range(4):
                coords[i, 0] = float(coords_json[i]['x'])
                coords[i, 1] = float(coords_json[i]['y'])
                coords[i, 2] = float(coords_json[i]['z'])
        except ValueError as exc:
            raise AxesControllerException(
                "Invalid coordinate value", exc) from None

        return coords

    async def get_light_intensity(self) -> int:
        """
        Return the current light intensity in the range [0...255].
        """
        if not self._config.is_light_controller:
            raise AxesControllerException(
                "Axes controller is no light controller")

        if not self.is_connected:
            raise AxesControllerConnectionException(
                "Axes controller not connected")

        # Read the value from the controller board
        response = await self._send_command("M375")
        match = re.match(r'^(\d+).*', response)
        if match:
            return int(match.group(0))
        return -1

    async def set_light_intensity(self, light_intensity: int) -> None:
        """
        Set the light intensity of the LED stripe to the given intensity.

        If the controller board is not configured as light controller this
        method has no effect!

        :param light_intensity: The light intensity to set in the range of [0...255]
        :type light_intensity: int
        """
        min_intensity = self.MIN_LIGHT_INTENSITY
        max_intensity = self.MAX_LIGHT_INTENSITY
        if not min_intensity <= light_intensity <= max_intensity:
            raise ValueError("Light intensity must be in the range [0...255]")

        await self._send_command(self.G_CODE_SET_LIGHT_INTENSITY.format(intensity=light_intensity))
        # Required so that the call is blocking
        await self._send_command("M375")

    @staticmethod
    def _format_position(x: float = None, y: float = None,
                         z: float = None) -> str:
        """
        Creates a formatted string of position coordinates that
        can be used for G-codes like G0 or G1.

        Values which are not set, are skipped so e.g. if only
        the x=100 and y=200 values are set, the following string
        will be created: 'X100 Y200'

        :param x: The X axis position
        :type x: float
        :param y: The y axis position
        :type y: float
        :param z: The z axis position
        :type z: float

        :return: The formatted position string in the format
                 'X... Y... Z...'.
        :rtype: str
        """
        position_string = ""
        if x is not None:
            position_string += f"X{x:3.4f} "
        if y is not None:
            position_string += f"Y{y:3.4f} "
        if z is not None:
            position_string += f"Z{z:3.4f} "

        return position_string

    async def _send_command(self, command: str) -> str:
        """
        Sends a given command to the axes control board

        This command blocks until an 'ok' or 'error' response
        from the board is received.

        :param command: The command string to send
        :type command: str
        :return: The response of the control board
        :rtype: str
        """
        if not self.is_connected:
            raise AxesControllerConnectionException(
                "Axes controller board not connected")

        await self._command_lock.acquire()
        try:
            return await self._send_controller_board_command(command,
                                                             self._usb_device,
                                                             self._config.baud_rate)
        finally:
            self._command_lock.release()

    @classmethod
    async def _send_controller_board_command(cls, command: str, usb_device: str,
                                             baud_rate: int = 115200,
                                             timeout: Optional[float] = None) -> str:
        """
        Sends a given command to an axes control board

        This command blocks until an 'ok' or 'error' response
        from the board is received.

        :param command: The command string to send
        :type command: str
        :param usb_device: USB serial to communicate with
        :type usb_device: str
        :param baud_rate: UART baud rate, defaults to 115200
        :type baud_rate: int
        :return: The response of the control board
        :rtype: str
        """
        # Send the command
        cls.log.debug("Sending command: %s", command)

        # Setup the final command
        command_with_delimiter = command + cls.COMMAND_DELIMITER

        # Wait for response
        response_string = ""
        matcher = re.compile(r"(.*\n)*ok\n$")
        matcher_error = re.compile(r"(.*\n)*Error:(.*)")

        # Poll UART
        async for line in send_uart_command(command_with_delimiter,
                                            usb_device,
                                            encoding="utf-8",
                                            baud_rate=baud_rate,
                                            command_delimiter=cls.COMMAND_DELIMITER,
                                            response_delimiter=cls.RESPONSE_DELIMITER,
                                            timeout=timeout):
            # Check whether a complete response has been received
            response_string += line
            if matcher.match(response_string) \
                    or matcher_error.match(response_string):
                break

        return response_string
