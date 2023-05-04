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
from dataclasses import dataclass
from typing import List

import numpy as np
from pydantic import Field
from quart import Blueprint, current_app
from quart_schema import validate_response, validate_request, tag

from proboter.fields import NumpyArray
from proboter.tasks import TaskProcessor, CalibrateProbeTask, CalibrateProbeTaskParameter, \
    CalibrateProbeTaskResult
from proboter.model import ReferenceBoardConfig, ProbeConfig, ProbeCalibrationConfig
from proboter.hardware import Proboter, Probe, ProbeStatus, ProbeType

from .utils import ApiTags, ApiException, ApiErrorResponse, inject_probe, inject_proboter, \
    inject_task_processor


log = logging.getLogger(__name__)

bp = Blueprint('probe', __name__, url_prefix="/probe")


@dataclass
class ProbeMoveRequest:
    """
    Probe move request
    """
    position: NumpyArray = Field(default_factory=lambda: np.zeros(3),
                                 np_shape=3)
    feed: float = Field(gt=0, default=1000)
    is_global: bool = False


@dataclass
class ProbeConfigUpdateRequest:
    """
    Probe configuration update request
    """
    name: str = Field()
    tmat_to_glob: NumpyArray = Field(np_shape=(4, 4))
    pos_x_safety_position: NumpyArray = Field(np_shape=3)
    neg_x_safety_position: NumpyArray = Field(np_shape=3)


@dataclass
class ProbeConfigResponse(ProbeConfigUpdateRequest):
    """
    Probe configuration
    """
    probe_type: ProbeType = Field()
    order_index: int = Field()

    @staticmethod
    def from_config(config: ProbeConfig) -> "ProbeConfigResponse":
        """
        Create an API response from a given probe configuration
        :rtype: ProbeConfigResponse
        """
        return ProbeConfigResponse(name=config.name,
                                   probe_type=config.probe_type,
                                   order_index=config.order_index,
                                   tmat_to_glob=config.tmat_to_glob,
                                   pos_x_safety_position=config.pos_x_safety_position,
                                   neg_x_safety_position=config.neg_x_safety_position)


@dataclass
class ProbeCalibrationConfigUpdateRequest:
    """
    Probe calibration configuration update request
    """
    calibration_feed: float = Field(gt=0)
    home_before_calibration: bool = Field()
    initial_probe_positions: NumpyArray = Field(np_shape=(4, 3))


@dataclass
class ProbeCalibrationConfigResponse(ProbeCalibrationConfigUpdateRequest):
    """
    Probe calibration configuration
    """
    @staticmethod
    def from_config(config: ProbeCalibrationConfig) \
            -> "ProbeCalibrationConfigResponse":
        """
        Create an API response from a given probe calibration configuration
        :rtype: ProbeCalibrationConfigResponse
        """
        home = config.home_before_calibration
        init_pos = config.initial_probe_positions
        return ProbeCalibrationConfigResponse(calibration_feed=config.calibration_feed,
                                              home_before_calibration=home,
                                              initial_probe_positions=init_pos)


@dataclass
class ProbeCalibrationResponse:
    """
    Multi-probe calibration result container
    """
    results: List[CalibrateProbeTaskResult]


@bp.route('/<probe_type>', methods=["GET"])
@validate_response(ProbeStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe(must_be_connected=False)
async def get_probe_status(probe: Probe) -> ProbeStatus:
    """
    Return the status of a single probe of the current PROBoter instance
    """
    log.info("Probe '%s' status request received", probe.config.probe_type)
    return probe.status


@bp.route('/<probe_type>/config', methods=["GET"])
@validate_response(ProbeConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe(must_be_connected=False)
async def get_probe_config(probe: Probe) -> ProbeConfigResponse:
    """
    Return a probe's configuration
    """
    log.info("Probe '%s' config request received", probe.config.probe_type)
    config = await ProbeConfig.get_by_id(probe.config.id)
    return ProbeConfigResponse.from_config(config)


@bp.route('/<probe_type>/config', methods=["PUT"])
@validate_request(ProbeConfigUpdateRequest)
@validate_response(ProbeConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe(must_be_connected=False)
async def update_probe_config(probe: Probe, data: ProbeConfigUpdateRequest) -> ProbeConfigResponse:
    """
    Update a probe's configuration
    """
    log.info("Probe '%s' update request received", probe.config.probe_type)
    config = await ProbeConfig.get_by_id(probe.config.id)

    # Update entries
    config.name = data.name
    config.tmat_to_glob = data.tmat_to_glob
    config.pos_x_safety_position = data.pos_x_safety_position
    config.neg_x_safety_position = data.neg_x_safety_position
    await config.save()

    # Reconnect / reload the PROBoter hardware so that the
    # new configuration is applied
    await current_app.reconnect_proboter()

    return ProbeConfigResponse.from_config(config)


@bp.route('/<probe_type>/calibration-config', methods=["GET"])
@validate_response(ProbeCalibrationConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe(must_be_connected=False)
async def get_probe_calibration_config(probe: Probe) -> ProbeCalibrationConfigResponse:
    """
    Return a probe's default calibration configuration
    """
    log.info("Probe '%s' calibration config request received",
             probe.config.probe_type)
    config = await ProbeConfig.get_by_id(probe.config.id)
    calibration_config = await config.calibration_config
    return ProbeCalibrationConfigResponse.from_config(calibration_config)


@bp.route('/<probe_type>/calibration-config', methods=["PUT"])
@validate_request(ProbeCalibrationConfigUpdateRequest)
@validate_response(ProbeCalibrationConfigResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe(must_be_connected=False)
async def update_probe_calibration_config(probe: Probe, data: ProbeCalibrationConfigUpdateRequest) \
        -> ProbeCalibrationConfigResponse:
    """
    Update a probe's calibration configuration
    """
    log.info("Probe '%s' calibration config update request received",
             probe.config.probe_type)
    config = await ProbeConfig.get_by_id(probe.config.id)
    calibration_config = await config.calibration_config

    # Update entries
    calibration_config.calibration_feed = data.calibration_feed
    calibration_config.home_before_calibration = data.home_before_calibration
    calibration_config.initial_probe_positions = data.initial_probe_positions
    await calibration_config.save()

    return ProbeCalibrationConfigResponse.from_config(calibration_config)


@bp.route('/<probe_type>/home', methods=["POST"])
@validate_response(ProbeStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe()
async def home_probe(probe: Probe) -> ProbeStatus:
    """
    Home the probe
    """
    log.info("Probe '%s' home request received", probe.config.probe_type)
    await probe.home()
    return probe.status


@bp.route('/<probe_type>/move', methods=["POST"])
@validate_request(ProbeMoveRequest)
@validate_response(ProbeStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe()
async def move_probe(probe: Probe, data: ProbeMoveRequest) -> ProbeStatus:
    """
    Move the probe
    """
    log.info("Probe '%s' move request received", probe.config.probe_type)
    log.info(data)
    # Global / local system mapping if required
    # Move commands are always executed in the common GLOBAL system
    if data.is_global:
        await probe.move_to_global_position(position=data.position,
                                            feed=data.feed)
    else:
        await probe.move_to_local_position(position=data.position,
                                           feed=data.feed)

    return probe.status


@bp.route('/<probe_type>/calibrate', methods=["POST"])
@validate_request(CalibrateProbeTaskParameter)
@validate_response(ProbeCalibrationResponse, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.PROBE])
@inject_probe()
@inject_proboter()
@inject_task_processor()
async def calibrate_probe(task_processor: TaskProcessor,
                          proboter: Proboter,
                          probe: Probe,
                          data: CalibrateProbeTaskParameter) -> ProbeCalibrationResponse:
    """
    Perform a calibration of a single probe by electrically probing a reference board
    """
    log.info("Probe '%s' calibration request received",
             probe.config.probe_type)
    log.info(data)

    # Fetch the reference board
    board_config = await ReferenceBoardConfig.get_by_id(data.reference_board)
    if board_config is None:
        raise ApiException("Reference board not found")

    # Calibrate the probe
    results = []
    for i in range(data.num_calibration_runs):
        log.info('Running calibration run %d of %d',
                 i + 1, data.num_calibration_runs)
        task = CalibrateProbeTask(data, probe, proboter, board_config)
        results.append(await task_processor.execute_task(task))

    return ProbeCalibrationResponse(results)
