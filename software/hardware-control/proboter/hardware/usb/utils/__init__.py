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

import asyncio
import logging
import termios
from typing import AsyncGenerator, Optional

import serial_asyncio

from .usb_monitor import UsbMonitor

log = logging.getLogger(__name__)


async def send_uart_command(cmd: str, device_name: str,
                            encoding: str = "ascii",
                            baud_rate: int = 115200,
                            command_delimiter: str = "\n",
                            response_delimiter: str = "\n",
                            send_delay: Optional[float] = None,
                            timeout: Optional[float] = None) -> AsyncGenerator:
    """
    Send a single command to an external device over UART

    :param cmd: Command to send
    :type cmd: str
    :param device_name: Name / path of the TTY device to use
    :type device_name: str
    :param encoding: Encoding used to encode the command / decode the response, defaults to "ascii"
    :type encoding: str, optional
    :param baud_rate: UART baud rate, defaults to 115200
    :type baud_rate: int, optional
    :param command_delimiter: Command delimiter, defaults to "\n". The delimiter is automatically
                              appended to the specified command.
    :type command_delimiter: str, optional
    :param response_delimiter: Response delimiter, defaults to "\n". This delimiter is used to
                               identify the end of a response sent by the device.
    :type response_delimiter: str, optional
    :param send_delay: Optional delay between the time the connection to the device is established
                       and the time the command is sent to the device, defaults to None
    :type send_delay: Optional[float], optional
    :param timeout: Max. time to wait for a response, defaults to None
    :type timeout: Optional[float], optional
    :return: An async. generator that generates a value for each individual received response.
    :rtype: AsyncGenerator
    :yield: Single device response. The end of a response is determined by the `response_delimiter`
            parameter.
    :rtype: Iterator[AsyncGenerator]
    """
    # Fixes Arduino auto-reset issues!!
    with open(device_name, encoding="ascii") as device_handle:
        attrs = termios.tcgetattr(device_handle)
        attrs[2] = attrs[2] & ~termios.HUPCL
        termios.tcsetattr(device_handle, termios.TCSAFLUSH, attrs)

    # Open a connection to the USB serial
    log.debug("Connecting to USB serial %s@%d", device_name, baud_rate)
    reader: asyncio.StreamReader = None
    writer: asyncio.StreamWriter = None
    reader, writer = await serial_asyncio.open_serial_connection(
        url=device_name,
        baudrate=baud_rate,
        timeout=1,
        dsrdtr=None)
    log.debug("Connection established")

    if send_delay is not None:
        await asyncio.sleep(send_delay)

    # Send the command
    cmd = bytearray(cmd.encode(encoding))
    cmd += command_delimiter.encode(encoding)
    log.debug("Sending command: %s", cmd)
    writer.write(cmd)
    await writer.drain()

    # Receive the response
    delimiter = response_delimiter.encode(encoding)
    log.debug("Starting response receival using delimiter %s", delimiter)
    try:
        while True:
            response = bytearray()
            if timeout is not None:
                response += await asyncio.wait_for(reader.readuntil(delimiter), timeout)
            else:
                response += await reader.readuntil(delimiter)
            log.debug("Received response chunk: %s", response)
            response += delimiter
            yield response.decode(encoding)
    finally:
        writer.close()
