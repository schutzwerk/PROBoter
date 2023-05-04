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
from asyncio import Queue
from typing import List, AsyncGenerator


class EventBus:
    """
    Simple implementation of an event bus
    """

    log = logging.getLogger(__module__)

    def __init__(self):
        self._event_queues: List[Queue] = []

    async def emit_event(self, event: object) -> None:
        """
        Emit an event

        Fist, the handler that are registered for the specific event
        class are executed. Then all global event handlers are executed
        in the order they have been registered.

        :param event: Event to emit
        :type event: object
        """
        self.log.debug("Emitting event")
        for event_queue in self._event_queues:
            await event_queue.put(event)

    async def events(self) -> AsyncGenerator[object, None]:
        """
        Return the events emitted on the event bus as an async. generator

        :return: Event generator
        :rtype: AsyncGenerator[object, None]
        """
        event_queue = Queue()
        self._event_queues.append(event_queue)
        try:
            while True:
                yield await event_queue.get()
        finally:
            self._event_queues.remove(event_queue)
