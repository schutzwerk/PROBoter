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


from typing import Callable

from proboter.model import UartInterfaceAdapterConfig
from proboter.hardware import UartInterfaceAdapter, UartDataReceivedEvent, \
    UartInterfaceAdapterConnectionException


class SimulationUartInterfaceAdapter(UartInterfaceAdapter):
    """
    Simulation of a UART interface adapter

    The implementation mimics an echo device that returns the received data
    """

    def __init__(self, config: UartInterfaceAdapterConfig,
                 on_new_uart_data: Callable[[UartDataReceivedEvent], None] = None):
        UartInterfaceAdapter.__init__(self, config,
                                      on_new_uart_data=on_new_uart_data)

    async def start(self) -> None:
        """
        Initialize the connection to the UART interface adapter
        """
        self.status.connected = True
        self._update_status(self.status)

    async def stop(self) -> None:
        """
        Release the UART interface adapter and frees all blocked resources
        """
        self.status.connected = False
        self._update_status(self.status)

    async def open(self, baud_rate: int) -> None:
        """
        Open the UART connection
        """
        self.status.open = True
        self._update_status(self.status)

    async def close(self) -> None:
        """
        Close a previously opened the UART connection
        """
        self.status.open = False
        self._update_status(self.status)

    async def send_data(self, data: str) -> None:
        """
        Send data to the target via the UART interface

        :param data: Data to send
        :type data: str
        """
        if not self.status.open:
            raise UartInterfaceAdapterConnectionException(
                "UART connection not open")
        # Echo the data back
        self.log.info("Sending UART command: %s", data)
        await self._new_uart_data_received(data.encode("utf-8"))
