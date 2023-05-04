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


import json
import asyncio
import logging

from quart import Blueprint, websocket

from proboter.event_bus import EventBus
from proboter.hardware import NewCameraFrameEvent, UartDataReceivedEvent

from .utils import inject_event_bus, event_to_json


log = logging.getLogger(__name__)

bp = Blueprint('events', __name__, url_prefix="/events")


@ bp.websocket('')
@ inject_event_bus()
async def get_camera_feed(event_bus: EventBus):
    """
    Global PROBoter event endpoint
    """
    log.info("Event websocket connection received")
    tx_task = None
    try:
        # Create task that polls events from the event bus
        # and publish them to the connected client
        async def publish_events_to_ws_client(ws, bus):
            async for event in bus.events():
                if not isinstance(event, (NewCameraFrameEvent,
                                          UartDataReceivedEvent)):
                    json_event = event_to_json(event)
                    log.debug("Sending event to client: %s", json_event)
                    await ws.send(json_event)
        tx_task = asyncio.create_task(publish_events_to_ws_client(websocket,
                                                                  event_bus))

        # Wait for client commands
        while True:
            cmd_raw = await websocket.receive()
            log.debug("Event request received from client: %s", cmd_raw)

            try:
                # Parse JSON command
                cmd = json.loads(cmd_raw)
                # React to ping requests with pong responses
                if "name" in cmd and cmd["name"] == "ping":
                    log.debug("Client PING received -> sending PONG response")
                    await websocket.send(json.dumps({"name": "pong"}))
            except json.JSONDecodeError:
                log.error("Received malformed client WS message")

    finally:
        log.info("Websocket connection to events endpoint closed")
        if tx_task is not None:
            tx_task.cancel()
