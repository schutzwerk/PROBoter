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

from typing import Tuple

from proboter.model import SignalMultiplexerConfig, SignalMultiplexerChannel
from proboter.hardware import SignalMultiplexer, SignalMultiplexerChannelSwitchState, \
    SignalMultiplexerChannelDigitalLevel


class SimulationSignalMultiplexer(SignalMultiplexer):
    """
    A signal multiplexer simulation
    """

    def __init__(self, config: SignalMultiplexerConfig):
        SignalMultiplexer.__init__(self, config)
        self._switch_states = [SignalMultiplexerChannelSwitchState.DIGITAL,
                               SignalMultiplexerChannelSwitchState.DIGITAL,
                               SignalMultiplexerChannelSwitchState.DIGITAL,
                               SignalMultiplexerChannelSwitchState.DIGITAL]
        self._digital_levels = [SignalMultiplexerChannelDigitalLevel.LOW,
                                SignalMultiplexerChannelDigitalLevel.LOW,
                                SignalMultiplexerChannelDigitalLevel.LOW,
                                SignalMultiplexerChannelDigitalLevel.LOW]
        self._pull_states = [SignalMultiplexerChannelDigitalLevel.LOW,
                             SignalMultiplexerChannelDigitalLevel.LOW,
                             SignalMultiplexerChannelDigitalLevel.LOW,
                             SignalMultiplexerChannelDigitalLevel.LOW]

    async def start(self):
        """
        Set up the connection to the signal multiplexer board
        """
        self.status.connected = True
        await self._update_status()

    async def stop(self) -> None:
        """
        Shutdown the multiplexer board
        """
        self.status.connected = False
        await self._update_status()

    async def get_switch_states(self) -> Tuple[SignalMultiplexerChannelSwitchState]:
        """
        Retrieves the current states of each channel
        """
        return tuple(self._switch_states)

    async def get_digital_levels(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Return the current digital logic levels for all channels

        :return: Ordered list of digital channel levels
        :rtype: Tuple[SignalMultiplexerChannelDigitalLevel]
        """
        return tuple(self._digital_levels)

    async def get_pull_states(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Retrieves a list of the current levels of each channel
        """
        return tuple(self._pull_states)

    async def test_channel(self, channel: SignalMultiplexerChannel) \
            -> SignalMultiplexerChannelDigitalLevel:
        """
        Return the current level of a given input channel

        :param channel: The input channel to test in the range of [0,3]
        :type channel: int
        :return: The current level of the input pin
        :rtype: SignalMultiplexerChannelDigitalLevel
        """
        return self._digital_levels[channel.value - 1]

    async def pull_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Actively pull a given input channel to a HIGH current level

        :param channel: The input channel to pull
        :type channel: Channel
        """
        self._pull_states[channel.value -
                          1] = SignalMultiplexerChannelDigitalLevel.HIGH
        self._digital_levels[channel.value -
                             1] = SignalMultiplexerChannelDigitalLevel.HIGH
        await self._update_status()

    async def release_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Release a previously pulled input channel

        The input channel is then pulled to a LOW level with
        a pull-down resistor

        :param channel: The input channel to release in the range of [0,3]
        :type channel: Channel
        """
        self._pull_states[channel.value -
                          1] = SignalMultiplexerChannelDigitalLevel.LOW
        self._digital_levels[channel.value -
                             1] = SignalMultiplexerChannelDigitalLevel.LOW
        await self._update_status()

    async def connect_to_digital(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connects the given signal channel to the
        digital measurement circuit

        :param channel: The signal channel to connect in the range of [0,3]
        :type channel: Channel
        """
        self._switch_states[channel.value -
                            1] = SignalMultiplexerChannelSwitchState.DIGITAL
        await self._update_status()

    async def connect_to_analog(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connect a given input channel to one of the two analogue outputs

        Input channels 1 or 2 are switched to the analogue measurement channel A.
        Input channels 3 or 4 are switched to the analogue measurement channel B.

        :param channel: The input channel to connect to the analogue output.
        :type channel: SignalMultiplexerChannel
        """
        if channel == SignalMultiplexerChannel.ONE:
            other = SignalMultiplexerChannel.TWO
            new_value = SignalMultiplexerChannelSwitchState.ANALOG_A
        elif channel == SignalMultiplexerChannel.TWO:
            other = SignalMultiplexerChannel.ONE
            new_value = SignalMultiplexerChannelSwitchState.ANALOG_A
        elif channel == SignalMultiplexerChannel.THREE:
            other = SignalMultiplexerChannel.FOUR
            new_value = SignalMultiplexerChannelSwitchState.ANALOG_B
        else:
            other = SignalMultiplexerChannel.THREE
            new_value = SignalMultiplexerChannelSwitchState.ANALOG_B

        # Simulated switch of the requested channel to the analogue output
        self._switch_states[channel.value - 1] = new_value
        self._pull_states[channel.value -
                          1] = SignalMultiplexerChannelDigitalLevel.LOW
        self._digital_levels[channel.value -
                             1] = SignalMultiplexerChannelDigitalLevel.LOW

        # Simulated switch to the coupled input channel to the digital logic
        self._switch_states[other.value -
                            1] = SignalMultiplexerChannelSwitchState.DIGITAL

        await self._update_status()
