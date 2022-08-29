# Copyright (C) 2022  SCHUTZWERK GmbH
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

from .analysis import api as ns_analysis


# Setup the API
api_bp = Blueprint('api', __name__)

# API version 1
apiv1_bp = Blueprint('apiv1', __name__, url_prefix='/v1')
api_bp.register_blueprint(apiv1_bp)

apiv1 = Api(apiv1_bp,
            title="Voltage signal analysis API v1",
            version="1.0",
            description=("Interpretation of voltage signals as "
                         "data transmission protocol"),
            validate=True)

# Register the API endpoints
apiv1.add_namespace(ns_analysis)


def api_index():
    """
    Return the default route to the SwaggerUI
    """
    return redirect(url_for('apiv1.doc'))
