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
from quart_schema import validate_response, tag

from proboter.hardware import LightController, LightControllerStatus

from .utils import ApiTags, ApiErrorResponse, inject_light_controller


log = logging.getLogger(__name__)

bp = Blueprint('light', __name__, url_prefix="/light")


@bp.route('', methods=["GET"])
@validate_response(LightControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.LIGHT_CONTROLLER])
@inject_light_controller(must_be_connected=False)
async def get_light_status(light_controller: LightController) -> LightControllerStatus:
    """
    Get the current light status
    """
    log.info("Light status request received")
    return light_controller.status


@bp.route('/on', methods=["POST"])
@validate_response(LightControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.LIGHT_CONTROLLER])
@inject_light_controller()
async def switch_light_on(light_controller: LightController):
    """
    Switch the light on
    """
    log.info("Light switch ON request received")
    await light_controller.switch_on()
    return light_controller.status


@bp.route('/off', methods=["POST"])
@validate_response(LightControllerStatus, 200)
@validate_response(ApiErrorResponse, 500)
@tag([ApiTags.LIGHT_CONTROLLER])
@inject_light_controller()
async def switch_light_off(light_controller: LightController):
    """
    Switch the light off
    """
    log.info("Light switch OFF request received")
    await light_controller.switch_off()
    return light_controller.status
