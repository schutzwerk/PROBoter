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
import asyncio
import logging
from typing import Callable

import serial_asyncio

from proboter.model import UartInterfaceAdapterConfig
from proboter.hardware import UartInterfaceAdapter, UartInterfaceAdapterConnectionException, \
    UartDataReceivedEvent


class UsbUartInterfaceAdapter(UartInterfaceAdapter):
    """
    Implementation that use a real UART / TTL to USB adapter to
    communicate with a target device via UART
    """
    log = logging.getLogger(__module__)

    def __init__(self, config: UartInterfaceAdapterConfig,
                 on_new_uart_data: Callable[[UartDataReceivedEvent, ], None] = None):
        """
        Initialize a new USB UART adapter
        """
        UartInterfaceAdapter.__init__(self, config,
                                      on_new_uart_data)

        self._usb_device = None
        self._command_lock = asyncio.locks.Lock()
        self._uart_poll_task = None
        self._uart_reader: asyncio.StreamReader = None
        self._uart_writer: asyncio.StreamWriter = None

    async def start(self) -> None:
        """
        Connect to the underlying device via the serial interface

        The USB device matching the vendor / model ID and UUID is
        automatically determined during the connection setup
        """
        # Stop all previously registered USB monitors
        await self.stop()

        # Check if device exists
        if not os.path.exists(self.config.usb_device_name):
            self.log.warning("Configured USB UART adapter device not found")
            self.status.connected = False
            self._usb_device = None
        else:
            self.log.info("Using USB UART adapter device device %s",
                          self.config.usb_device_name)
            self.status.connected = True
            self._usb_device = self.config.usb_device_name
            # Sync with the hardware
            await self.sync()

        self._update_status(self.status)

    async def stop(self) -> None:
        """
        Release the UART interface adapter and frees all blocked resources
        """
        await self.close()
        self._usb_device = None
        self.status.connected = False
        self._update_status(self.status)

    async def open(self, baud_rate: int) -> None:
        """
        Open the UART connection
        """
        self.log.debug("Connecting to USB serial %s@%d",
                       self._usb_device,
                       baud_rate)
        self._uart_reader, self._uart_writer = await serial_asyncio.open_serial_connection(
            url=self._usb_device,
            baudrate=baud_rate,
            timeout=1)

        # Set up a UART data polling task
        self._uart_poll_task = asyncio.create_task(self._poll_uart_data())
        self.log.debug("Connection established")

        self.status.open = True
        self._update_status(self.status)

    async def close(self) -> None:
        """
        Close a previously opened the UART connection
        """
        # Cancel the UART data poll task
        if self._uart_poll_task is not None:
            self._uart_poll_task.cancel()
            await self._uart_poll_task
            self._uart_poll_task = None

        # Close the UART connection
        if self._uart_writer is not None:
            self._uart_writer.close()
            self._uart_reader = None
            self._uart_writer = None

        self.status.open = False
        self._update_status(self.status)

    async def send_data(self, data):
        """
        Sends a given command to the UART interface over
        the established serial connection.

        :param command: The command string to send
        :type command: str
        :return: The response of the control board
        :rtype: str
        """
        if self._uart_writer is None:
            raise UartInterfaceAdapterConnectionException(
                "UART connection not open")

        async with self._command_lock:
            self.log.debug("Sending UART data to target: %s", data)
            self._uart_writer.write(data.encode("utf-8"))
            await self._uart_writer.drain()
            self.log.debug("UART data successfully sent")

    async def _poll_uart_data(self) -> None:
        """
        Read data from the UART connection
        """
        chunk_size = 100
        rx_timeout = 0.1

        # TODO Check if this is really necessary here!
        # pylint: disable=broad-exception-caught
        try:
            while True:
                data = bytearray()
                # Poll <chunk_size> bytes from the UART or
                # until no data has been received for <rx_timeout>
                # seconds
                while len(data) < chunk_size:
                    try:
                        data += await asyncio.wait_for(self._uart_reader.read(1),
                                                       rx_timeout)
                    except asyncio.exceptions.TimeoutError:
                        break

                if len(data) > 0:
                    # Notify about data RX
                    await self._new_uart_data_received(data)
        except Exception as exc:
            self.log.error("UART poll error %s: %s", type(exc), exc)
        except asyncio.CancelledError:
            ...
        finally:
            self.log.info(("Shutting down UART poll task"))
