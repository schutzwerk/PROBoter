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
from abc import abstractmethod
from typing import Callable, Tuple

from proboter.model import UartInterfaceAdapterConfig, SignalMultiplexerChannel

from .events import UartInterfaceAdapterStatus, UartDataReceivedEvent
from .hardware_unit import HardwareUnit


class UartInterfaceAdapter(HardwareUnit[UartInterfaceAdapterConfig,
                                        UartInterfaceAdapterStatus]):
    """
    Interface for a UART interface adapter that allows the
    communication with a target
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: UartInterfaceAdapterConfig,
                 on_new_uart_data: Callable[[UartDataReceivedEvent, ],
                                            None] = None):
        HardwareUnit.__init__(self, config, UartInterfaceAdapterStatus())

        self._on_new_uart_data = on_new_uart_data
        self._is_emitting_events = True

    @ property
    def connected(self) -> bool:
        """
        Whether the UART interface adapter hardware is connected
        """
        return self.status.connected

    @ property
    def status(self) -> UartInterfaceAdapterStatus:
        """
        Current status of the UART interface adapter
        """
        return self._status

    @ property
    def rx_pin_channel(self) -> SignalMultiplexerChannel:
        """
        Return the signal multiplexer digital channel the UART RX is connected to
        """
        return self._config.rx_multiplexer_channel

    @ property
    def tx_pin_channel(self) -> SignalMultiplexerChannel:
        """
        Return the signal multiplexer digital channel the UART TX is connected to
        """
        return self._config.tx_multiplexer_channel

    @ property
    def ground_pin_channels(self) -> Tuple[SignalMultiplexerChannel]:
        """
        Return an iterable collection of signal multiplexer channels to which
        the UART adapter's ground pin is connected to
        """
        return (self._config.ground_1_multiplexer_channel,
                self._config.ground_2_multiplexer_channel)

    @abstractmethod
    async def start(self) -> None:
        """
        Initialize the connection to the UART interface adapter
        """

    @abstractmethod
    async def stop(self) -> None:
        """
        Release the UART interface adapter and frees all blocked resources
        """

    @abstractmethod
    async def open(self, baud_rate: int) -> None:
        """
        Open the UART connection
        """

    @abstractmethod
    async def close(self) -> None:
        """
        Close a previously opened the UART connection
        """

    @abstractmethod
    async def send_data(self, data: str) -> None:
        """
        Send data to the target via the UART interface

        :param data: Data to send
        :type data: str
        """

    def _update_status(self, new_status: UartInterfaceAdapterStatus) -> None:
        """
        Update the UART interface adapter status and inform observers
        by invoking the `on_status_changed` callback

        :param new_status: The new UART interface adapter status
        :type new_status: UartInterfaceAdapterStatus
        """
        self._status = new_status

    async def _new_uart_data_received(self, uart_data: bytes) -> None:
        """
        Inform observers about newly received UART data

        :param uart_data: Received UART data
        :type uart_data: bytes
        """
        self.log.debug("UART data received: 0x%s", uart_data.hex(" "))

        try:
            # Decode the received data and put it in the receive queue
            data_str = uart_data.decode("utf-8")

            # Notify about data RX
            if self._on_new_uart_data is not None:
                self.log.debug("Emitting UartDataReceivedEvent")
                await self._on_new_uart_data(
                    UartDataReceivedEvent(data=data_str))
        except UnicodeDecodeError:
            self.log.error("Invalid UART data received: %s", uart_data.hex(' ').upper())
