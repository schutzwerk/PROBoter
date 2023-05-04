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

from quart import Blueprint, Response, redirect, url_for
from quart_schema import validate_response, hide

from proboter.model import EntityNotFoundException

from .utils import ApiTags, ApiException, ApiErrorResponse

from .light import bp as bp_light
from .signal_multiplexer import bp as bp_signal_multiplexer
from .uart_interface import bp as bp_uart_interface
from .target_power import bp as bp_target_power
from .proboter import bp as bp_proboter
from .probe import bp as bp_probe
from .probing import bp as bp_probing
from .reference_board import bp as bp_reference_board
from .camera_static import bp as bp_camera_static
from .events import bp as bp_events
from .tasks import bp as bp_tasks
from .demo_mode import bp as bp_demo_mode

# Setup the API
api_bp = Blueprint('api', __name__)

# API version 1
apiv1_bp = Blueprint('apiv1', __name__, url_prefix='/v1')
api_bp.register_blueprint(apiv1_bp)

# Add endpoint blueprints
apiv1_bp.register_blueprint(bp_light)
apiv1_bp.register_blueprint(bp_target_power)
apiv1_bp.register_blueprint(bp_probe)
apiv1_bp.register_blueprint(bp_proboter)
apiv1_bp.register_blueprint(bp_probing)
apiv1_bp.register_blueprint(bp_uart_interface)
apiv1_bp.register_blueprint(bp_signal_multiplexer)
apiv1_bp.register_blueprint(bp_reference_board)
apiv1_bp.register_blueprint(bp_camera_static)
apiv1_bp.register_blueprint(bp_events)
apiv1_bp.register_blueprint(bp_tasks)
apiv1_bp.register_blueprint(bp_demo_mode)

# API documentation
api_tags = [
    {
        "name": ApiTags.LIGHT_CONTROLLER,
        "description": "PROBoter light control"
    },
    {
        "name": ApiTags.SIGNAL_MULTIPLEXER,
        "description": "PROBoter signal multiplexer board"
    },
    {
        "name": ApiTags.UART_INTERFACE,
        "description": "PROBoter UART adapter interface"
    },
    {
        "name": ApiTags.TARGET_POWER_CONTROLLER,
        "description": "PROBoter target power controller"
    },
    {
        "name": ApiTags.PROBE,
        "description": "PROBoter probe control"
    },
    {
        "name": ApiTags.PROBING,
        "description": "High-level probing tasks"
    },
    {
        "name": ApiTags.REFERENCE_BOARD,
        "description": "Reference board definitions"
    },
    {
        "name": ApiTags.CAMERA_STATIC,
        "description": "PROBoter static camera control"
    },
    {
        "name": ApiTags.DEMO_MODE,
        "description": "PROBoter demo mode tasks"
    }
]


@apiv1_bp.errorhandler(ApiException)
@validate_response(ApiErrorResponse, 500)
def handle_api_exception(exc: ApiException) -> ApiErrorResponse:
    """
    Return a custom message and 500 status code
    """
    return ApiErrorResponse(reason=exc.reason,
                            description=exc.description), 500


@apiv1_bp.errorhandler(EntityNotFoundException)
@validate_response(ApiErrorResponse, 500)
def handle_entity_not_found_exception(_: EntityNotFoundException) -> ApiErrorResponse:
    """
    Return a custom message and 500 status code
    """
    return ApiErrorResponse(reason="Entity not found",
                            description=""), 500

@hide
def api_docs_url() -> Response:
    """
    Return the default route to the API Swagger documentation
    """
    return redirect('/docs')
