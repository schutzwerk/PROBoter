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

from dataclasses import dataclass


@dataclass
class TaskScheduledEvent:
    """
    Event that is emitted when a new task has been
    scheduled for execution
    """
    # ID of the task
    id: int
    # Name of the task
    name: str


@dataclass
class TaskStartedEvent:
    """
    Event that is emitted when execution of a new
    task is started by the task processor
    """
    # ID of the task
    id: int
    # Name of the task
    name: str


@dataclass
class TaskChangedEvent:
    """
    Event that is emitted when the state of a
    task has changed
    """
    # ID of the task
    id: int
    # Name of the task
    name: str


@dataclass
class TaskFinishedEvent:
    """
    Event that is emitted when execution of a
    task has finished
    """
    # ID of the task
    id: int
    # Name of the task
    name: str
    # Whether the task has been cancelled
    cancelled: bool = False
    # Whether the task execution failed due to an error
    had_error: bool = False
