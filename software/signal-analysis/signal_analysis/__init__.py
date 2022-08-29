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

import os
import logging

from flask import Flask
from flask_cors import CORS

from .api import api_bp, api_index
from .analysis import SignalAnalysisService


def logging_setup() -> None:
    """
    Basic logging setup
    """
    logging.basicConfig(level=logging.DEBUG,
                        format="%(levelname)s %(message)s")
    logging.addLevelName(logging.DEBUG, "[*]")
    logging.addLevelName(logging.INFO, "[*]")
    logging.addLevelName(logging.WARNING, "[W]")
    logging.addLevelName(logging.ERROR, "[E]")
    return logging.getLogger('main')


def create_app(test_config: dict = None) -> Flask:
    """
    Create a Flask instance serving the signal analyis application

    :param test_config: Optional configuration parameters passed to the
                        Flask application
    :type test_config: [dict], optional
    :return: Flask application
    :rtype: Flask
    """
    # Setup logging
    logging_setup()

    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        JSON_SORT_KEYS=True,
        RESTX_VALIDATE=True
    )

    if test_config is None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register the API blueprint
    app.register_blueprint(api_bp, url_prefix='/api')

    # Default route redirects to the API documentation
    app.add_url_rule('/', view_func=api_index)

    # Enable CORS
    CORS(app,
         resources={r"/api/*": {"origins": "*"}})

    # Inject a singleton of the signal analyis service
    app.analysis_service = SignalAnalysisService()

    return app
