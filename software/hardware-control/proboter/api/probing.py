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

from proboter.tasks import UartProbingMoveTaskResult, UartProbingMoveTaskParameter, \
    UartProbingMoveTask, ProbeElectricalConnectivityTask, ProbeElectricalConnectivityParameter, \
    ProbeElectricalConnectivityResult, TaskProcessor, MeasureVoltageSignalsTask, \
    MeasureVoltageSignalsParameter, MeasureVoltageSignalsResult

from .utils import ApiTags, ApiErrorResponse, inject_task_processor, inject_proboter


log = logging.getLogger(__name__)

bp = Blueprint('probing', __name__, url_prefix="/probing")


@bp.route('/electrical-connectivity', methods=["POST"])
@validate_request(ProbeElectricalConnectivityParameter)
@validate_response(ProbeElectricalConnectivityResult, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBING])
@inject_task_processor()
@inject_proboter()
async def probe_electrical_connectivity(proboter: Proboter,
                                        task_processor: TaskProcessor,
                                        data: ProbeElectricalConnectivityParameter) \
        -> ProbeElectricalConnectivityResult:
    """
    Probe a set of pins / pads for electrical connectivity
    """
    log.info("Electrical connectivity probing request received")
    log.info(data)
    task = ProbeElectricalConnectivityTask(data, proboter)

    return await task_processor.execute_task(task)


@bp.route('/measure-voltage-signals', methods=["POST"])
@validate_request(MeasureVoltageSignalsParameter)
@validate_response(MeasureVoltageSignalsResult, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBING])
@inject_task_processor()
@inject_proboter()
async def measure_voltage_levels(proboter: Proboter,
                                 task_processor: TaskProcessor,
                                 data: MeasureVoltageSignalsParameter) \
        -> MeasureVoltageSignalsResult:
    """
    Measure voltage levels at given pins / pads
    """
    log.info("Voltage signal measurement request received")
    log.info(data)
    task = MeasureVoltageSignalsTask(data, proboter)

    return await task_processor.execute_task(task)


@bp.route('/uart', methods=["POST"])
@validate_request(UartProbingMoveTaskParameter)
@validate_response(UartProbingMoveTaskResult, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBING])
@inject_task_processor()
@inject_proboter()
async def uart_probe_move_to_pins(proboter: Proboter,
                                  task_processor: TaskProcessor,
                                  data: UartProbingMoveTaskParameter) \
        -> UartProbingMoveTaskResult:
    """
    Move the UART probes to the global PCB coordinates specified in the request
    """
    log.info("UART probe move request received")
    task = UartProbingMoveTask(data, proboter)

    return await task_processor.execute_task(task)
