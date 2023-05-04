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

from quart import Blueprint
from quart_schema import validate_response, validate_request, tag

from proboter.hardware import Proboter

from proboter.tasks import TaskProcessor, ProbePartyTask, ProbePartyParameter


from .utils import ApiTags, ApiErrorResponse, TaskScheduledResponse, \
    inject_task_processor, inject_proboter


log = logging.getLogger(__name__)

bp = Blueprint('demo_mode', __name__, url_prefix="/demo-mode")


@bp.route('/probe-party', methods=["POST"])
@validate_request(ProbePartyParameter)
@validate_response(TaskScheduledResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.DEMO_MODE])
@inject_task_processor()
@inject_proboter()
async def probe_electrical_connectivity(proboter: Proboter,
                                        task_processor: TaskProcessor,
                                        data: ProbePartyParameter) \
        -> TaskScheduledResponse:
    """
    Let the probes run in an endless loop for demonstration purposes
    """
    log.info("Probe Party request received")
    log.info(data)
    task = ProbePartyTask(data, proboter)

    task_id = await task_processor.schedule_task(task)
    return TaskScheduledResponse(task_id)
