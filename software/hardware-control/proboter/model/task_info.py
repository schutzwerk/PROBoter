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

from enum import Enum

from tortoise import fields

from .entity import Entity


class TaskStatus(str, Enum):
    """
    Task status
    """
    # The task has been created and is scheduled for execution
    SCHEDULED = "SCHEDULED"
    # The task is currently executed
    RUNNING = "RUNNING"
    # Task execution has successfully finished
    FINISHED = "FINISHED"
    # Task execution has been cancelled
    CANCELLED = "CANCELLED"
    # Task execution failed with error
    ERRORED = "ERRORED"


class TaskInfo(Entity):
    """
    Information about a scheduled / executed task
    """
    # Id of the task
    id: int = fields.IntField(pk=True)
    # Name of the task
    name: str = fields.CharField(max_length=100, null=False)
    # Task status
    status: TaskStatus = fields.CharEnumField(TaskStatus,
                                              default=TaskStatus.SCHEDULED,
                                              max_length=10,
                                              null=False)
    # Progress
    progress: float = fields.FloatField(default=0.0, null=False)
    # Task parameter serialized as JSON
    parameter: str = fields.CharField(max_length=2000, null=True)
    # Task result serialized as JSON
    result: str = fields.CharField(max_length=2000, null=True)
    # Task error serialized as string
    error: str = fields.CharField(max_length=2000, null=True)
