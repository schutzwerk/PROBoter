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

import logging
from typing import Tuple
from abc import abstractmethod

from proboter.model import SignalMultiplexerConfig, SignalMultiplexerChannel, \
    ProbeType

from .hardware_unit import HardwareUnit
from .probe import Probe
from .exceptions import SignalMultiplexerException
from .events import SignalMultiplexerStatus, \
    SignalMultiplexerChannelSwitchState, SignalMultiplexerChannelDigitalLevel


class SignalMultiplexer(HardwareUnit[SignalMultiplexerConfig,
                                     SignalMultiplexerStatus]):
    """
    A signal multiplexer allowing to control the signal
    routing from the PROBoter probes to measurement equipment.

    The board also allows for simple level checks between multiple
    probes which e.g. can be used to detect if two probes are electrically
    connected.

    The communication with the board is done via a serial interface using a
    line based custom protocol.
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: SignalMultiplexerConfig):
        """
        Initialize a signal multiplexer board
        """
        HardwareUnit.__init__(self, config=config,
                              status=SignalMultiplexerStatus(id=config.id))

    @abstractmethod
    async def get_switch_states(self) -> Tuple[SignalMultiplexerChannelSwitchState]:
        """
        Retrieves the current states of each channel
        """

    @abstractmethod
    async def get_digital_levels(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Return the current digital logic levels for all channels

        :return: Ordered list of digital channel levels
        :rtype: Tuple[SignalMultiplexerChannelDigitalLevel]
        """

    @abstractmethod
    async def get_pull_states(self) -> Tuple[SignalMultiplexerChannelDigitalLevel]:
        """
        Retrieves a list of the current levels of each channel
        """

    @abstractmethod
    async def pull_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Actively pull a given input channel to a HIGH current level

        :param channel: The input channel to pull
        :type channel: Channel
        """

    @abstractmethod
    async def release_channel(self, channel: SignalMultiplexerChannel) -> None:
        """
        Release a previously pulled input channel

        The input channel is then pulled to a LOW level with
        a pull-down resistor

        :param channel: The input channel to release in the range of [0,3]
        :type channel: Channel
        """

    @abstractmethod
    async def connect_to_digital(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connects the given signal channel to the
        digital measurement circuit

        :param channel: The signal channel to connect in the range of [0,3]
        :type channel: SignalMultiplexerChannel
        """

    @abstractmethod
    async def connect_to_analog(self, channel: SignalMultiplexerChannel) -> None:
        """
        Connect a given input channel to one of the two analogue outputs

        Input channels 1 or 2 are switched to the analogue measurement channel A.
        Input channels 3 or 4 are switched to the analogue measurement channel B.

        :param channel: The input channel to connect to the analogue output.
        :type channel: SignalMultiplexerChannel
        """

    @abstractmethod
    async def test_channel(self, channel: SignalMultiplexerChannel) \
            -> SignalMultiplexerChannelDigitalLevel:
        """
        Return the current level of a given input channel

        :param channel: The input channel to test in the range of [0,3]
        :type channel: int
        :return: The current level of the input pin
        :rtype: SignalMultiplexerChannelDigitalLevel
        """

    def get_channel_by_probe(self, probe: Probe) -> SignalMultiplexerChannel:
        """
        Determine the channel of the multiplexer a given probe is connected to

        :param probe: The probe to find the matching channel
        :type probe: Probe
        :return: The signal channel in the range [0,3] the probe is connected to
        :rtype: int
        """
        if probe.id == self.config.channel_1_probe_id:
            return SignalMultiplexerChannel.ONE
        if probe.id == self.config.channel_2_probe_id:
            return SignalMultiplexerChannel.TWO
        if probe.id == self.config.channel_3_probe_id:
            return SignalMultiplexerChannel.THREE
        if probe.id == self.config.channel_4_probe_id:
            return SignalMultiplexerChannel.FOUR
        raise SignalMultiplexerException(
            f"Probe {probe.id:d} is not connected to the multiplexer")

    async def get_probe_type_by_channel(
            self, channel: SignalMultiplexerChannel) -> ProbeType:
        """
        Determine the probe a given signal multiplexer channel is connected to

        :param channel: The channel to find the matching probe
        :type channel: SignalMultiplexerChannel
        :return: The probe type the channel is connected to
        :rtype: int
        """
        await self.config.fetch_related("channel_1_probe")
        await self.config.fetch_related("channel_2_probe")
        await self.config.fetch_related("channel_3_probe")
        await self.config.fetch_related("channel_4_probe")

        if channel == SignalMultiplexerChannel.ONE:
            return self.config.channel_1_probe.probe_type
        if channel == SignalMultiplexerChannel.TWO:
            return self.config.channel_2_probe.probe_type
        if channel == SignalMultiplexerChannel.THREE:
            return self.config.channel_3_probe.probe_type
        if channel == SignalMultiplexerChannel.FOUR:
            return self.config.channel_4_probe.probe_type
        raise SignalMultiplexerException(
            f"Invalid signal multiplexer channel {channel}")

    async def get_switch_state(self, channel: SignalMultiplexerChannel) \
            -> SignalMultiplexerChannelSwitchState:
        """
        Returns the current state of the given channel
        """
        self.log.debug("Get switch state of channel %s", channel)
        return await self.get_switch_states()[channel.value - 1]

    async def test_probe(self, probe: Probe) -> SignalMultiplexerChannelDigitalLevel:
        """
        Return the current voltage level of a given probe

        :param probe: The probe to test
        :type probe: Probe
        :return: The digital current voltage level of the probe
        :rtype: SignalMultiplexerChannelDigitalLevel
        """
        return await self.test_channel(self.get_channel_by_probe(probe))

    async def test_probe_connection(self, test_probe: Probe, master_probe: Probe,
                                    pulse_test: bool = False) -> bool:
        """
        Test whether two probes are electrically connected

        To test the connection, the master probe is actively pulled HIGH.
        If the test / slave probe shows the same voltage level, the probes
        are assumed to be connected.

        :param test_probe: The test / slave probe. The voltage level
                           of this probe is only measured during the test.
        :type test_probe: Probe
        :param master_probe: The master probe. During the test, the voltage
                             level of this probe is actively pulled to HIGH.
        :type master_probe: Probe
        :param pulse_test: Whether to use a pulsed signal to verify the connection.
                           This feature is currently not implemented!!
        :type pulse_test: bool
        :return: Whether the probes are connected (True) or not (False)
        :rtype: bool
        """
        test_channel = self.get_channel_by_probe(test_probe)
        master_channel = self.get_channel_by_probe(master_probe)
        if pulse_test:
            raise NotImplementedError()

        # Assert that the test channel is by default LOW
        if await self.test_channel(test_channel) != SignalMultiplexerChannelDigitalLevel.LOW:
            raise SignalMultiplexerException(("Test channel must be LOW prior "
                                              "to a connection measurement"))

        # Pull the power channel
        await self.pull_channel(master_channel)
        # Test the level at the test channel again
        channel_level = await self.test_channel(test_channel)
        connected = channel_level == SignalMultiplexerChannelDigitalLevel.HIGH
        # Release the power channel
        await self.release_channel(master_channel)
        return connected

    async def pull_probe(self, probe: Probe) -> None:
        """
        Actively pull the input channel the probe is
        connected to to a HIGH level

        :param probe: The probe to pull
        :type probe: Probe
        """
        channel = self.get_channel_by_probe(probe)
        await self.pull_channel(channel)
        await self._update_status()

    async def release_probe(self, probe: Probe) -> None:
        """
        Release a previously pulled input channel of the probe

        The input channel is then pulled to a LOW level with
        a pull-down resistor

        :param probe: The probe to release
        :type probe: Probe
        """
        channel = self.get_channel_by_probe(probe)
        await self.release_channel(channel)
        await self._update_status()

    async def connect_to_digital_probe(self, probe: Probe) -> None:
        """
        Connects the given signal channel associated to a probe to the
        digital measurement circuit

        :param probe: The probe to connect to the digital measurement logic
        :type probe: Probe
        """
        channel = self.get_channel_by_probe(probe)
        await self.connect_to_digital(channel)
        await self._update_status()

    async def release_all(self) -> None:
        """
        Release all input channels. Each input channel is pulled to
        a LOW level with a pull-down resistor
        """
        for channel in SignalMultiplexerChannel:
            await self.release_channel(channel)
        await self._update_status()

    async def _update_status(self) -> None:
        """
        Queries the current status of the signal multiplexer hardware
        and caches it in the current instance

        Caching is done due to performance reasons!

        Also, observers are informed about the current state by invoking the
        `on_state_changed` callback.
        """
        # Default values
        switch_states = SignalMultiplexerStatus.channel_switch_states
        channel_digital_levels = SignalMultiplexerStatus.channel_digital_levels
        channel_pull_states = SignalMultiplexerStatus.channel_pull_states

        if self.status.connected:
            # Query the current status from the hardware
            switch_states = await self.get_switch_states()
            channel_digital_levels = await self.get_digital_levels()
            channel_pull_states = await self.get_pull_states()

        self.status.id = self.config.id
        self.status.channel_switch_states = switch_states
        self.status.channel_digital_levels = channel_digital_levels
        self.status.channel_pull_states = channel_pull_states
