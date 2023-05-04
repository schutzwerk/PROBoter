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
import logging
from typing import Tuple
from asyncio.locks import Lock

from proboter.model import SignalMultiplexerConfig, SignalMultiplexerChannel
from proboter.hardware import SignalMultiplexer, SignalMultiplexerException, \
    SignalMultiplexerChannelSwitchState, SignalMultiplexerChannelDigitalLevel

from .utils import send_uart_command


class UsbSignalMultiplexer(SignalMultiplexer):
    """
    A signal multiplexer allowing to control the signal
    routing from the PROBoter probes to measurement equipment.

    The board also allows for simple level checks between multiple
    probes which e.g. can be used to detect if two probes are electrically
    connected.

    The communication with the board is done via a serial interface using a
    line based custom protocol.
    """
    # Protocol / command definition
    CMD_DELIMITER = "\r\n"
    CMD_TEST_CHANNEL = 'test {inputchannel:d}'
    CMD_PULL_CHANNEL = 'pull {inputchannel:d}'
    CMD_RELEASE_CHANNEL = 'release {inputchannel:d}'
    CMD_SWITCH_A = 'switchA {inputchannel:d}'
    CMD_SWITCH_B = 'switchB {inputchannel:d}'
    CMD_SWITCH_DIGITAL = 'switchDigital {inputchannel:d}'
    CMD_PULSE_CONNECTION_TEST = 'pulsetest {testchannel:d} {powerchannel:d}'
    CMD_GET_SWITCH_STATES = 'getSwitchState'
    CMD_GET_DIGITAL_STATES = 'getDigitalStates'
    CMD_GET_PULL_STATES = 'getPullStates'
    CMD_GET_CHANNEL_STATUS = 'status {inputchannel:d}'

    logger = logging.getLogger(__module__)

    def __init__(self, config: SignalMultiplexerConfig):
        SignalMultiplexer.__init__(self, config)
        # The USB monitor used to detect USB hot-plug events
        self._usb_monitor = None
        # Name of the USB device used to communicate with the multiplexer board
        self._usb_device = None
        # Lock to ensure that only a single command is sent to the board
        self._command_lock = Lock()

    async def start(self):
        """
        Set up the connection to the signal multiplexer board
        """
        # Stop all previously registered USB monitors
        await self.stop()

        # Check if device exists
        if not os.path.exists(self.config.usb_device_name):
            self.log.warning("Configured signal multiplexer device not found")
            self.status.connected = False
            self._usb_device = None
        else:
            self.log.info("Using signal multiplexer device device %s",
                          self.config.usb_device_name)
            self.status.connected = True
            self._usb_device = self.config.usb_device_name

        await self._update_status()

    async def stop(self) -> None:
        """
        Shutdown the multiplexer board
        """
        self.status.connected = False
        self._usb_device = None
        await self._update_status()

    async def get_switch_states(self) -> Tuple[SignalMultiplexerChannelSwitchState]:
        """
        Retrieves the current states of each channel
        """
        response = await self._send_command(self.CMD_GET_SWITCH_STATES)
        states = [SignalMultiplexerChannelSwitchState(state)
                  for state in response.split()]
        return tuple(states)

    async def get_digital_levels(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Return the current digital logic levels for all channels

        :return: Ordered list of digital channel levels
        :rtype: Tuple[SignalMultiplexerChannelDigitalLevel]
        """
        response = await self._send_command(self.CMD_GET_DIGITAL_STATES)
        states = []
        for state in response.split():
            states.append(SignalMultiplexerChannelDigitalLevel.HIGH if int(
                state) == 1 else SignalMultiplexerChannelDigitalLevel.LOW)
        return tuple(states)

    async def get_pull_states(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Retrieves a list of the current levels of each channel
        """
        response = await self._send_command(self.CMD_GET_PULL_STATES)
        states = []
        for state in response.split():
            states.append(SignalMultiplexerChannelDigitalLevel.HIGH if int(
                state) == 1 else SignalMultiplexerChannelDigitalLevel.LOW)
        return tuple(states)

    async def pull_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Actively pull a given input channel to a HIGH current level

        :param channel: The input channel to pull
        :type channel: Channel
        """
        cmd = self.CMD_PULL_CHANNEL.format(inputchannel=channel.value)
        await self._send_command(cmd)
        await self._update_status()

    async def release_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Release a previously pulled input channel

        The input channel is then pulled to a LOW level with
        a pull-down resistor

        :param channel: The input channel to release in the range of [0,3]
        :type channel: Channel
        """
        cmd = self.CMD_RELEASE_CHANNEL.format(inputchannel=channel.value)
        await self._send_command(cmd)
        await self._update_status()

    async def connect_to_digital(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connects the given signal channel to the
        digital measurement circuit

        :param channel: The signal channel to connect in the range of [0,3]
        :type channel: Channel
        """
        cmd = self.CMD_SWITCH_DIGITAL.format(inputchannel=channel.value)
        await self._send_command(cmd)
        await self._update_status()

    async def connect_to_analog(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connect a given input channel to one of the two analogue outputs

        Input channels 1 or 2 are switched to the analogue measurement channel A.
        Input channels 3 or 4 are switched to the analogue measurement channel B.

        :param channel: The input channel to connect to the analogue output.
        :type channel: SignalMultiplexerChannel
        """

        if channel in (SignalMultiplexerChannel.ONE,
                       SignalMultiplexerChannel.TWO):
            cmd = self.CMD_SWITCH_A.format(inputchannel=channel.value)
            other = SignalMultiplexerChannel.ONE \
                if channel == SignalMultiplexerChannel.TWO else SignalMultiplexerChannel.TWO
        else:
            cmd = self.CMD_SWITCH_B.format(inputchannel=channel.value)
            other = SignalMultiplexerChannel.THREE \
                if channel == SignalMultiplexerChannel.FOUR else SignalMultiplexerChannel.FOUR
        await self.connect_to_digital(other)
        await self._send_command(cmd)
        await self._update_status()

    async def test_channel(self, channel: SignalMultiplexerChannel) \
            -> SignalMultiplexerChannelDigitalLevel:
        """
        Return the current level of a given input channel

        :param channel: The input channel to test in the range of [0,3]
        :type channel: int
        :return: The current level of the input pin
        :rtype: SignalMultiplexerChannelDigitalLevel
        """
        # Switch to the digital measurement circuit
        # TODO Restore the state after the measurement
        await self.connect_to_digital(channel)

        # Measure the current level
        cmd = self.CMD_TEST_CHANNEL.format(inputchannel=channel.value)
        response = await self._send_command(cmd)

        # Validate the response
        if response == '0':
            return SignalMultiplexerChannelDigitalLevel.LOW

        if response == '1':
            return SignalMultiplexerChannelDigitalLevel.HIGH

        raise SignalMultiplexerException(f"Invalid response from multiplexer board: {response}")

    async def _send_command(self, command: str) -> str:
        """
        Sends a given command to the multiplexer board over
        the established serial connection.

        This command blocks until a command delimiter is received from the board.

        :param command: The command string to send
        :return: The response of the control board
        """
        # Check the connection status
        if not self.status.connected:
            raise SignalMultiplexerException(
                "Multiplexer board is not connected")

        # Send the command
        await self._command_lock.acquire()
        self.logger.debug("Sending command: %s", command)
        response = None
        response_ctr = 0
        try:
            async for response_line in send_uart_command(command,
                                                         device_name=self._usb_device,
                                                         baud_rate=self.config.baud_rate,
                                                         command_delimiter="\n"):
                response_ctr += 1
                if response_ctr >= 2:
                    response = response_line.strip()
                    break
            self.logger.debug("Received response: %s", response)
        except OSError:
            raise SignalMultiplexerException(
                "Error sending command to multiplexer board") from None
        finally:
            self._command_lock.release()

        return response
