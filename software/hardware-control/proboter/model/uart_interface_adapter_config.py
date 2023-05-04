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
from .signal_multiplexer_config import SignalMultiplexerChannel


# Longer lines allowed for readability
# pylint: disable=line-too-long
class UartInterfaceAdapterConfig(Entity):
    """
    Configuration for a generic UART-to-USB adapter
    """
    # Id of the UART interface adapter
    id: int = fields.IntField(pk=True)
    # The USB port to which the UART adapter is connected. If this value is set
    # to None, the hardware layer should use the USB vendor and model information
    # to find the correct USB device.
    usb_device_name: str = fields.CharField(100, null=False)
    # First channel of the signal multiplexer the RX pin is connected to
    rx_multiplexer_channel_1 = fields.IntEnumField(
        SignalMultiplexerChannel, null=False)
    # Second channel of the signal multiplexer the RX pin is connected to
    rx_multiplexer_channel_2 = fields.IntEnumField(
        SignalMultiplexerChannel, null=False)
    # First channel of the signal multiplexer the TX pin is connected to
    tx_multiplexer_channel_1 = fields.IntEnumField(
        SignalMultiplexerChannel, null=False)
    # Second channel of the signal multiplexer the TX pin is connected to
    tx_multiplexer_channel_2 = fields.IntEnumField(
        SignalMultiplexerChannel, null=False)
    # The ID of the PROBoter configuration the probe belongs to
    proboter: fields.OneToOneRelation["ProboterConfig"] = fields.OneToOneField("models.ProboterConfig",
                                                                               related_name="uart_interface_adapter",
                                                                               null=False)
