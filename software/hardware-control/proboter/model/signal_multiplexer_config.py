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
from typing import List

from tortoise import fields

from .entity import Entity
from .probe_config import ProbeConfig


class SignalMultiplexerChannel(int, Enum):
    """
    Digital channels of a signal multiplexer
    """
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4

    @staticmethod
    def min() -> int:
        """
        Return the index of the first signal multiplexer channel
        rtype: int
        """
        return SignalMultiplexerChannel.ONE

    @staticmethod
    def max() -> int:
        """
        Return the index of the last signal multiplexer channel
        rtype: int
        """
        return SignalMultiplexerChannel.FOUR

    @staticmethod
    def from_int(channel_index: int) -> 'SignalMultiplexerChannel':
        """
        Return a SignalMultiplexerChannel instance corresponding to a given channel index
        rtype: SignalMultiplexerChannel
        """
        assert SignalMultiplexerChannel.min() <= channel_index <= SignalMultiplexerChannel.max()
        return SignalMultiplexerChannel(channel_index)

    @classmethod
    def channel_ids(cls) -> List[int]:
        """
        Return a sorted list of all signal multiplexer channel indices
        rtype: int
        """
        return sorted(map(lambda t: t.value, cls.__members__.values()))

    @classmethod
    def channels(cls) -> List[int]:
        """
        Return a sorted list of all signal multiplexer channel indices
        rtype: int
        """
        return sorted(list(cls.__members__.values()),
                      key=lambda entry: entry.value)


# Longer lines allowed for readability
# pylint: disable=line-too-long
class SignalMultiplexerConfig(Entity):
    """
    Configuration for the custom signal multiplexer board
    """
    # pylint: disable=too-few-public-methods
    # The multiplexer config ID
    id: int = fields.IntField(pk=True)
    # The name of signal multiplexer board
    name: str = fields.CharField(100, null=False)
    # The baudrate used for the communication via the
    # serial console
    baud_rate: int = fields.IntField(null=False)
    # The USB port to which the signal multiplexer is connected. If this value is set
    # to None, the hardware layer should use the USB vendor and model information
    # to find the correct USB device.
    usb_device_name: str = fields.CharField(100, null=False)
    # Probe connected to channel 1 of the multiplexer
    channel_1_probe: fields.ForeignKeyRelation["ProbeConfig"] = fields.ForeignKeyField("models.ProbeConfig",
                                                                                       related_name="signal_multiplexer_channel_1",
                                                                                       null=True)
    # Probe connected to channel 2 of the multiplexer
    channel_2_probe: fields.ForeignKeyRelation["ProbeConfig"] = fields.ForeignKeyField("models.ProbeConfig",
                                                                                       related_name="signal_multiplexer_channel_2",
                                                                                       null=True)
    # Probe connected to channel 3 of the multiplexer
    channel_3_probe: fields.ForeignKeyRelation["ProbeConfig"] = fields.ForeignKeyField("models.ProbeConfig",
                                                                                       related_name="signal_multiplexer_channel_3",
                                                                                       null=True)
    # Probe connected to channel 4 of the multiplexer
    channel_4_probe: fields.ForeignKeyRelation["ProbeConfig"] = fields.ForeignKeyField("models.ProbeConfig",
                                                                                       related_name="signal_multiplexer_channel_4",
                                                                                       null=True)
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.OneToOneRelation["ProboterConfig"] = fields.OneToOneField("models.ProboterConfig",
                                                                               related_name="signal_multiplexer",
                                                                               null=False)
