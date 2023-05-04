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

from typing import TypeVar, Generic, Optional

from proboter.model import TaskInfo
from proboter.event_bus import EventBus

from .events import TaskChangedEvent

T = TypeVar("T")
S = TypeVar("S")


class Task(Generic[S, T]):
    """
    Base class for all commands

    The event bus instance used for status update notifications
    is injected by the task processor!
    """

    def __init__(self, name: str, params: S):
        """
        Initialize a new new task

        :param name: Task name
        :type name: str
        :param params: Task parameters
        :type params: S
        """
        self._params: S = params
        self._info = TaskInfo(name=name)
        self._event_bus: EventBus = None

    @property
    def params(self) -> S:
        """
        Task parameter

        :rtype: S
        """
        return self._params

    @property
    def info(self) -> TaskInfo:
        """
        Task status information

        :rtype: TaskInfo
        """
        return self._info

    @property
    def event_bus(self) -> Optional[EventBus]:
        """
        Event bus instance that is used to notify
        about task status changes

        :rtype: Optional[EventBus]
        """
        return self._event_bus

    @event_bus.setter
    def event_bus(self, event_bus: Optional[EventBus]) -> None:
        """
        Event bus instance that is used to notify
        about task status changes

        :param event_bus: New event bus
        :type event_bus: Optional[EventBus]
        """
        self._event_bus = event_bus

    async def run(self) -> T:
        """
        Execute the task
        """

    async def _status_changed(self) -> None:
        """
        Emit an event on the event bus and persist the new task state
        """
        # Persist the current state
        await self.info.save()

        # Notify about the status change
        if self.event_bus is not None:
            await self.event_bus.emit_event(TaskChangedEvent(self.info.id,
                                                             self.info.name))
