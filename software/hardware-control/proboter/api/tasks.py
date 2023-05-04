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
from typing import List, Optional
from dataclasses import dataclass

from quart import Blueprint
from quart_schema import validate_response, tag

from proboter.tasks import TaskProcessor
from proboter.model import TaskInfo, TaskStatus

from .utils import ApiTags, ApiErrorResponse, ApiEmptyResponse, inject_task_processor


log = logging.getLogger(__name__)

bp = Blueprint('tasks', __name__, url_prefix="/tasks")


@dataclass
class TaskInfoResponse:
    """
    Task info response
    """
    id: int
    name: str
    status: TaskStatus
    progress: float
    parameter: Optional[str]
    result: Optional[str]
    error: Optional[str]

    @staticmethod
    def from_task_info(task_info: TaskInfo) -> "TaskInfoResponse":
        """
        Create an API response from a given task information object
        :rtype: TaskInfoResponse
        """
        return TaskInfoResponse(id=task_info.id,
                                name=task_info.name,
                                status=task_info.status.value,
                                progress=task_info.progress,
                                parameter=task_info.parameter,
                                result=task_info.result,
                                error=task_info.error)


@ dataclass
class TaskInfoListResponse:
    """
    Task info list response
    """
    tasks: List[TaskInfoResponse]


@ bp.route('', methods=["GET"])
@ validate_response(TaskInfoListResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.TASKS])
async def get_task_list():
    """
    Get all executed and scheduled tasks
    """
    log.info("Task task list request received")
    task_infos = await TaskInfo.get_all()
    return TaskInfoListResponse(list(TaskInfoResponse.from_task_info(info)
                                     for info in task_infos))


@ bp.route('/current', methods=["GET"])
@ validate_response(TaskInfoResponse, 200)
@ validate_response(ApiEmptyResponse, 204)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.TASKS])
@ inject_task_processor()
async def get_current_task(task_processor: TaskProcessor):
    """
    Get the current task if any
    """
    log.info("Current task request received")
    if task_processor.current_task is not None:
        task_info = task_processor.current_task.info
        return TaskInfoResponse.from_task_info(task_info), 200
    return ApiEmptyResponse(), 204


@ bp.route('/<int:task_id>', methods=["GET"])
@ validate_response(TaskInfoResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.TASKS])
async def get_task_by_id(task_id: int) -> TaskInfoResponse:
    """
    Get task by ID
    """
    log.info("Task get request received for task ID %d", task_id)
    task_info = await TaskInfo.get_by_id(task_id)
    return TaskInfoResponse.from_task_info(task_info)


@ bp.route('/cancel', methods=["POST"])
@ validate_response(ApiEmptyResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.TASKS])
@ inject_task_processor()
async def cancel_current_task(task_processor: TaskProcessor) -> ApiEmptyResponse:
    """
    Cancel the currently running task if any
    """
    log.info("Task cancel request received")
    await task_processor.cancel()
    return ApiEmptyResponse()


@ bp.route('/cancel/<int:task_id>', methods=["POST"])
@ validate_response(ApiEmptyResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.TASKS])
@ inject_task_processor()
async def cancel_task_by_id(task_processor: TaskProcessor, task_id: int) -> ApiEmptyResponse:
    """
    Cancel a task with a given ID
    """
    log.info("Task cancel request received for task ID %d",
             task_id)
    await task_processor.cancel_task(task_id)
    return ApiEmptyResponse()
