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

import asyncio
import logging

from quart import Blueprint
from quart_schema import validate_response, tag

from proboter.hardware import TargetPowerController, TargetPowerControllerStatus

from .utils import ApiTags, ApiErrorResponse, inject_power_controller


log = logging.getLogger(__name__)

bp = Blueprint('power-controller', __name__, url_prefix="/power-controller")


@bp.route('', methods=["GET"])
@validate_response(TargetPowerControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.TARGET_POWER_CONTROLLER])
@inject_power_controller(must_be_connected=False)
async def get_power_controller_status(power_controller: TargetPowerController) \
        -> TargetPowerControllerStatus:
    """
    Return the current PROBOter power status
    """
    log.info("Target power controller status request received")
    return power_controller.status


@bp.route('/on', methods=["POST"])
@validate_response(TargetPowerControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.TARGET_POWER_CONTROLLER])
@inject_power_controller()
async def switch_target_power_on(power_controller: TargetPowerController) \
        -> TargetPowerControllerStatus:
    """
    Switch the target power on
    """
    log.info("Switch target power ON request received")
    await power_controller.switch_power_on()
    return power_controller.status


@bp.route('/off', methods=["POST"])
@validate_response(TargetPowerControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.TARGET_POWER_CONTROLLER])
@inject_power_controller()
async def switch_target_power_off(power_controller: TargetPowerController) \
        -> TargetPowerControllerStatus:
    """
    Switch the target power off
    """
    log.info("Switch target power OFF request received")
    await power_controller.switch_power_off()
    return power_controller.status


@bp.route('/reset', methods=["POST"])
@validate_response(TargetPowerControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.TARGET_POWER_CONTROLLER])
@inject_power_controller()
async def reset_target(power_controller: TargetPowerController) \
        -> TargetPowerControllerStatus:
    """
    Reset the target by switching it off and on again
    """
    log.info("Reset target request received")
    await power_controller.switch_power_off()
    await asyncio.sleep(2)
    await power_controller.switch_power_on()
    return power_controller.status
