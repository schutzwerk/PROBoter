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
import asyncio
from dataclasses import dataclass

from quart import Blueprint, websocket
from quart_schema import validate_response, validate_querystring, tag

from proboter.event_bus import EventBus
from proboter.hardware import UartInterfaceAdapter, UartInterfaceAdapterStatus, \
    UartDataReceivedEvent

from .utils import ApiTags, ApiErrorResponse, \
    inject_event_bus, inject_uart_interface


log = logging.getLogger(__name__)

bp = Blueprint('uart-interface', __name__, url_prefix="/uart-interface")


@dataclass
class UartOpenParameter:
    """
    UART open parameter
    """
    baud_rate: int = 115200


@bp.route('/open', methods=["POST"])
@ validate_querystring(UartOpenParameter)
@validate_response(UartInterfaceAdapterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.UART_INTERFACE])
@inject_uart_interface()
async def open_uart_connection(uart_interface: UartInterfaceAdapter,
                               query_args: UartOpenParameter) -> UartInterfaceAdapterStatus:
    """
    Open the UART connection for data RX / TX
    """
    log.info("UART interface open request received")
    await uart_interface.open(query_args.baud_rate)
    return uart_interface.status


@bp.route('/close', methods=["POST"])
@validate_response(UartInterfaceAdapterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.UART_INTERFACE])
@inject_uart_interface()
async def close_uart_connection(uart_interface: UartInterfaceAdapter) \
        -> UartInterfaceAdapterStatus:
    """
    Close the UART connection
    """
    log.info("UART interface close request received")
    await uart_interface.close()
    return uart_interface.status


@bp.websocket('/shell')
@tag([ApiTags.UART_INTERFACE])
@inject_event_bus()
@inject_uart_interface()
async def uart_shell(uart_interface: UartInterfaceAdapter, event_bus: EventBus):
    """
    Websocket endpoint that exposes an interactive shell
    of the PROBoter's UART interface adapter
    """
    log.info("UART shell websocket connection received")
    tx_task = None

    # This is intended here because the Websocket should not be disrupted by
    # any error in the UART interface logic
    # pylint: disable=broad-exception-caught
    try:
        # Task to send UART data to the connected client
        async def send_uart_data_to_ws_client(ws):
            log.info("Start UART event data polling")
            try:
                async for event in event_bus.events():
                    if isinstance(event, UartDataReceivedEvent):
                        await ws.send(event.data)
            finally:
                log.info("Stopped UART event data polling")

        tx_task = asyncio.create_task(send_uart_data_to_ws_client(websocket))

        # UART command receival
        while True:
            cmd = await websocket.receive()
            log.info("UART data received from WS client: %s", cmd)
            await uart_interface.send_data(cmd)
    except Exception:
        log.error("UART shell websocket connection closed due to error")
    except asyncio.CancelledError:
        log.info("UART shell websocket connection closed by client")
    finally:
        if tx_task is not None:
            tx_task.cancel()
