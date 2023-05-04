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

from quart import Blueprint, current_app
from quart_schema import validate_response, validate_request, tag

from proboter.hardware import Proboter, ProboterStatus
from proboter.model import ProboterConfig
from proboter.tasks import MoveProboterTask, MoveProboterParameter, \
    MoveProboterResult, TaskProcessor

from .utils import ApiTags, ApiErrorResponse, inject_proboter, \
    inject_task_processor


log = logging.getLogger(__name__)

bp = Blueprint('proboter', __name__, url_prefix="/proboter")


@bp.route('', methods=["GET"])
@validate_response(ProboterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBOTER])
@inject_proboter()
async def get_proboter_status(proboter: Proboter) -> ProboterStatus:
    """
    Return the current PROBoter status
    """
    log.info("PROBoter status request received")
    return proboter.status


@bp.route('/home', methods=["POST"])
@validate_response(ProboterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBOTER])
@inject_proboter()
async def home_probter(proboter: Proboter) -> ProboterStatus:
    """
    Home the PROBoter hardware
    """
    log.info("PROBoter homing request received")
    await proboter.home()
    return proboter.status


@bp.route('/move', methods=["POST"])
@validate_request(MoveProboterParameter)
@validate_response(MoveProboterResult, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBOTER])
@inject_task_processor()
@inject_proboter()
async def move_proboter(proboter: Proboter, task_processor: TaskProcessor,
                        data: MoveProboterParameter) -> MoveProboterResult:
    """
    Move the PROBoter hardware
    """
    log.info("PROBoter moving request received")
    log.info(data)
    task = MoveProboterTask(data, proboter)
    return await task_processor.execute_task(task)


@bp.route('/clear-probing-area', methods=["POST"])
@validate_response(ProboterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBOTER])
@inject_proboter()
async def clear_proboter_probing_area(proboter: Proboter) -> ProboterStatus:
    """
    Clear the probing area by moving all probes to their safety positions
    """
    log.info("PROBoter clear probing area request received")
    await proboter.clear_probing_area()
    return proboter.status


@bp.route('/reconnect', methods=["POST"])
@validate_response(ProboterStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBOTER])
async def reconnect_proboter() -> ProboterStatus:
    """
    Reconnect the PROBoter hardware
    """
    log.info("PROBoter reconnect request received")

    # Reconnect the PROBoter hardware
    await current_app.reconnect_proboter()
    return current_app.proboter.status
