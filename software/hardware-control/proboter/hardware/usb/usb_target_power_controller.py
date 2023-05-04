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

import os
import re
import logging
from typing import Optional
from asyncio.locks import Lock

from proboter.event_bus import EventBus
from proboter.model import TargetPowerControllerConfig
from proboter.hardware import TargetPowerController, TargetPowerControllerNotConnectedException, \
    TargetPowerControllerException

from .utils import send_uart_command


class UsbTargetPowerController(TargetPowerController):
    """
    Target power controller that allows to switch the power
    of a device under test off and on

    The board also allows current measurements. However, this
    feature is not integrated yet!

    The communication with the board is done via a serial interface using a
    line based custom protocol.
    """
    # Protocol / command definition
    CMD_END_PATTERN = 'ok: %s'
    CMD_SWITCH_ON = 'switch-on'
    CMD_SWITCH_OFF = 'switch-off'
    CMD_MEASURE_CURRENT = 'measure-current'
    CMD_STATUS = 'status'
    CMD_CALIBRATE_ZERO_POINT = 'calibrate-zero-point'

    log = logging.getLogger(__module__)

    def __init__(self, config: TargetPowerControllerConfig,
                 event_bus: EventBus):
        TargetPowerController.__init__(self, config, event_bus)
        # Name of the USB device used to communicate with the multiplexer board
        self._usb_device = None
        # Lock to ensure that only a single command is sent to the board
        self._command_lock = Lock()

    @property
    def is_connected(self) -> bool:
        """
        Whether the USB target power controller is connected

        :rtype: bool
        """
        return self._usb_device is not None

    async def start(self):
        """
        Set up the connection to the signal multiplexer board
        """
        # Stop all previously registered USB monitors
        await self.stop()

        # Check if device exists
        if not os.path.exists(self.config.usb_device_name):
            self.log.warning("Configured target power controller"
                             " device not found")
            self.status.connected = False
            self._usb_device = None
        else:
            self.log.info("Using target power controller device device %s",
                          self.config.usb_device_name)
            self.status.connected = True
            self._usb_device = self.config.usb_device_name
            # Sync with the hardware
            await self.sync()

    async def stop(self) -> None:
        """
        Shutdown the multiplexer board
        """
        self.status.connected = False
        self._usb_device = None
        await self._status_changed()

    async def sync(self) -> None:
        """
        Force synchronization with the hardware's state
        """
        # TODO The send delay of 1.5 seconds is a dirty hack
        #      required because otherwise during the initial
        #      startup the Arduino does not capture the first
        #      command sent!
        status_response = await self._send_command(self.CMD_STATUS, 1.5)
        status_lines = [line.strip() for line in status_response.split("\n")
                        if ":" in line]
        status_dict = {}
        for line in status_lines:
            entries = [entry.strip() for entry in line.split(":")]
            assert len(entries) == 2
            status_dict[entries[0]] = entries[1]
        assert "relais" in status_dict
        self.status.on = int(status_dict["relais"]) > 0
        await self._status_changed()

    async def switch_power_on(self) -> None:
        """
        Turn the power on
        """
        self.log.info("Switching target power on")
        await self._send_command(self.CMD_SWITCH_ON)
        self.status.on = True
        await self._status_changed()

    async def switch_power_off(self) -> None:
        """
        Turn the power off
        """
        self.log.info("Switching target power off")
        await self._send_command(self.CMD_SWITCH_OFF)
        self.status.on = False
        await self._status_changed()

    async def _send_command(self, command: str, send_delay: Optional[float] = None) -> str:
        """
        Sends a given command to the target power controller board
        over the USB serial connection

        This command blocks until a command delimiter is received from the board.

        :param command: The command string to send
        :return: The response of the control board
        """
        # Check the connection status
        if not self.is_connected:
            raise TargetPowerControllerNotConnectedException(
                "Target power controller board not connected")
        # Send the command
        end_pattern = re.compile(self.CMD_END_PATTERN % command)
        response = ""
        async with self._command_lock:
            self.log.debug("Sending command: %s", command)
            try:
                async for response_line in send_uart_command(command,
                                                             device_name=self._usb_device,
                                                             baud_rate=self.config.baud_rate,
                                                             command_delimiter="\n",
                                                             response_delimiter="\n",
                                                             send_delay=send_delay):
                    self.log.debug(
                        "Received response: '%s'",
                        response_line.strip())
                    if end_pattern.match(response_line.strip()):
                        break
                    response += response_line.strip() + "\n"
                response = response.strip()
                self.log.debug("Received response: %s", response)
            except OSError:
                raise TargetPowerControllerException(
                    "Error sending command to target power controller board") from None

        return response
