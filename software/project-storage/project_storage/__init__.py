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

import os
import logging
from pathlib import Path

from flask import Flask
from flask_cors import CORS

from .api import apiv1_bp, api_index
from .model import db


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
    log = logging_setup()

    # Check for Flask instance folder overwrite
    instance_path = os.environ["FLASK_INSTANCE_PATH"] \
        if "FLASK_INSTANCE_PATH" in os.environ \
        else None
    log.info("Using instance path: %s", instance_path)

    # create and configure the app
    app = Flask(
        __name__,
        instance_path=instance_path,
        instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY="dev",
        JSON_SORT_KEYS=True,
        RESTX_VALIDATE=True,
        SQLALCHEMY_DATABASE_URI='sqlite:///' +
        str(Path(app.instance_path, 'pcb_data.sqlite').absolute()),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        # Load the instance config from environment variables
        app.config.from_prefixed_env()
    else:
        # Load the test config if passed in
        app.config.from_mapping(test_config)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    log.info("Storing data at: %s", app.config.get("SQLALCHEMY_DATABASE_URI"))

    # Register the API blueprint
    app.register_blueprint(apiv1_bp, url_prefix='/api/v1')

    # Default route redirects to the API documentation
    app.add_url_rule('/', view_func=api_index)

    # Setup SQLAlchemy
    db.init_app(app)

    # Initialize the database schema if required
    with app.app_context():
        # pylint: disable=locally-disabled, no-member
        # This is the preferred solution to check for table
        # existence. However, pylint has problems with the
        # Inspector returend by the 'inspect' function
        if not db.inspect(db.engine).has_table('pcb'):
            log.info("Initializing database schema")
            db.drop_all()
            db.create_all()
            log.info("Database initialized")
        else:
            log.info("Dabase already initialized")

    # Enable CORS
    CORS(app,
         resources={r"/api/*": {"origins": "*"}})

    return app
