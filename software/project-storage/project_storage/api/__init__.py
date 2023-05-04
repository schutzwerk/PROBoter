# Copyright (C) 2022 SCHUTZWERK GmbH
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

from flask_restx import Api
from flask import Blueprint, redirect, url_for

from .pcb import api as ns_pcb
from .pcb_pin import api as ns_pin
from .pcb_scan import api as ns_scan
from .pcb_network import api as ns_network
from .pcb_component import api as ns_component


# API version 1
apiv1_bp = Blueprint('apiv1', __name__)

apiv1 = Api(apiv1_bp,
            title="PCB project data storage API v1",
            version="1.0",
            doc="/doc/",
            description=("Manage PCB analysis / project data"),
            validate=True)

# Register the API endpoints
apiv1.add_namespace(ns_pcb, '/pcb')
apiv1.add_namespace(ns_pin, '/pcb')
apiv1.add_namespace(ns_scan, '/pcb')
apiv1.add_namespace(ns_network, '/pcb')
apiv1.add_namespace(ns_component, '/pcb')


def api_index():
    """
    Return the default route to the SwaggerUI
    """
    return redirect(url_for('apiv1.doc'))
