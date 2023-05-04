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

import os
import logging
from pathlib import Path

from quart import Quart, current_app
from quart.json.provider import DefaultJSONProvider
from quart_schema import QuartSchema
from quart_cors import cors

from tortoise.contrib.quart import register_tortoise

import cv2

import numpy as np

from .api import api_bp, api_docs_url, api_tags
from .cli import proboter_cli, initialize_db
from .event_bus import EventBus
from .model import ProboterConfig
from .hardware.usb import UsbProboterFactory
from .hardware.simulation import SimulationProboterFactory
from .tasks import Task, TaskProcessor
from .storage import StorageBackendConfig


def logging_setup() -> None:
    """
    Basic logging setup
    """
    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(message)s")
    logging.addLevelName(logging.DEBUG, "[*]")
    logging.addLevelName(logging.INFO, "[*]")
    logging.addLevelName(logging.WARNING, "[W]")
    logging.addLevelName(logging.ERROR, "[E]")

    logging.getLogger('tortoise').setLevel(logging.WARNING)
    logging.getLogger('aiosqlite').setLevel(logging.WARNING)

    return logging.getLogger('main')


logger = logging_setup()


async def app_startup():
    """
    Pre-server startup tasks
    """
    # Ensure that the database is initialized
    # TODO Improve database init check here!
    if not os.path.exists(Path(current_app.instance_path, 'proboter.sqlite').absolute()):
        logger.info("Seeding database")
        await initialize_db(current_app)
    else:
        logger.info("Database already seeded")

    # Start the PROBoter hardware
    await current_app.reconnect_proboter()

    # Start the task processor
    await current_app.task_processor.house_keeping()
    await current_app.task_processor.start()


async def app_shutdown():
    """
    Pre-server shutdown tasks
    """
    # Stop the task processor
    await current_app.task_processor.stop()

    # Shutdown the PROBoter hardware
    logger.info("Stopping PROBoter hardware")
    if current_app.proboter is not None:
        await current_app.proboter.stop()


async def reconnect_proboter():
    """
    (Re-)connect the PROBoter hardware with the current
    configuration stored in the database
    """
    if current_app.proboter is not None:
        logger.info("Stopping PROBoter hardware")
        await current_app.proboter.stop()

    # Load the active PROBoter configuration
    logger.info("Loading PROBoter hardware config")
    config = await ProboterConfig.get_active_config()
    logger.info("Using hardware config %s", config)

    # Start the PROBoter hardware
    logger.info("(Re-)Initializing PROBoter hardware")
    current_app.proboter = await current_app.proboter_factory.create_from_config(config,
                                                                                 autostart=False)
    await current_app.proboter.start()
    logger.info("PROBoter hardware (re-)connected successfully")


def create_app(test_config: dict = None) -> Quart:
    """
    Create a Quart instance serving the PROBoter hardware control application

    :param test_config: Optional configuration parameters passed to the
                    Quart application, defaults to None
    :type test_config: dict, optional
    :return: Quart application
    :rtype: Quart
    """
    # Check for Quart instance folder overwrite
    instance_path = Path(os.environ["QUART_INSTANCE_PATH"]).absolute() \
        if "QUART_INSTANCE_PATH" in os.environ \
        else None
    logger.info("Using instance path: %s", instance_path)

    # Setup the Quart app
    app = Quart(__name__, instance_path=instance_path)

    # Default app config
    app.config.from_mapping(
        HARDWARE_BACKEND="usb",
        SECRET_KEY="dev",
        JSON_SORT_KEYS=False,
        DATABASE_URI='sqlite:///' +
        str(Path(app.instance_path, 'proboter.sqlite').absolute()),
        # Statically included Swagger and Redocly files
        QUART_SCHEMA_SWAGGER_JS_URL="/static/swagger-ui-bundle.js",
        QUART_SCHEMA_SWAGGER_CSS_URL="/static/swagger-ui.min.css",
        QUART_SCHEMA_REDOC_JS_URL="/static/redoc.standalone.js",
        STORAGE_BACKEND_URL="http://localhost:5000/api/v1"
    )

    if test_config is not None:
        # Load test config if passed in
        app.config.from_mapping(test_config)
    else:
        # Load config from environment variables
        app.config.from_prefixed_env()

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # API documentation with Swagger / OpenAPI
    QuartSchema(app,
                info={"version": "1.0",
                      "title": "PROBoter hardware control API"
                      },
                convert_casing=True,
                tags=api_tags)

    # Create the singleton event bus instance
    app.event_bus = EventBus()

    # Create the singleton task processor
    app.task_processor = TaskProcessor(app.event_bus)

    # PROBoter hardware singleton
    app.proboter = None

    # Global function to (re-)connect the PROBoter hardware
    # TODO Move this to a better place!
    app.reconnect_proboter = reconnect_proboter

    # Configure the storage backend
    logger.info("Using storage backend URL: %s",
                app.config["STORAGE_BACKEND_URL"])
    StorageBackendConfig.BASE_URL = app.config["STORAGE_BACKEND_URL"]

    # Create the PROBoter hardware-related service(s)
    if app.config["HARDWARE_BACKEND"].lower() == "simulation":
        logger.info("Running with PROBoter hardware simulation")
        app.proboter_factory = SimulationProboterFactory(
            event_bus=app.event_bus)
    else:
        logger.info("Running with real PROBoter hardware")
        app.proboter_factory = UsbProboterFactory(event_bus=app.event_bus,
                                                  video_capture_factory=cv2.VideoCapture)

    # Custom ext. JSON conversion
    def convert_to_json(_, value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value

    DefaultJSONProvider.default = convert_to_json
    app.json_provider_class = DefaultJSONProvider

    # Register API blueprints (REST)
    app.url_map.strict_slashes = False
    app.register_blueprint(api_bp, url_prefix="/api")

    # Default route redirects to the API documentation
    app.add_url_rule('/', view_func=api_docs_url)

    # Enable CORS for all API endpoints
    cors(app, allow_origin="*")

    # Setup the database connection and ORM
    register_tortoise(
        app,
        db_url=app.config["DATABASE_URI"],
        modules={"models": ["proboter.model"]}
    )

    # Register custom CLI commands
    proboter_cli(app)

    # Register life cycle hooks
    app.before_serving(app_startup)
    app.after_serving(app_shutdown)

    return app


if __name__ == "__main__":
    create_app().run()
