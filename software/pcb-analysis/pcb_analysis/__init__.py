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
import atexit
import logging

from flask import Flask
from flask_cors import CORS

from .api import api_bp, api_index
from .encoders import EnhancedJsonEncoder
from .visual_analysis import AnalysisService
from .pin_detection import CvPipelinePinDetector, TensorflowPinDetector
from .chip_detection import TensorflowChipDetector, ColorBasedChipDetector


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
    Create a Flask instance serving the visual PCB analyis application

    :param test_config: Optional configuration parameters passed to the
                        Flask application
    :type test_config: [dict], optional
    :return: Flask application
    :rtype: Flask
    """
    # Setup logging
    logging_setup()

    # Setup the analysis service (singleton)
    analysis_service = AnalysisService()

    # Register the chip detectors
    analysis_service.add_chip_detector(name='Faster-RCNN',
                                       factory=lambda: TensorflowChipDetector(
                                            model=TensorflowChipDetector.FASTER_RCNN_PCB_CUSTOM),
                                       chip_detector_id='ded48437-36bc-4116-a374-1aaa6b0d7681')

    analysis_service.add_chip_detector(name='SSD',
                                       factory=lambda: TensorflowChipDetector(
                                           model=TensorflowChipDetector.SSD_PCB_CUSTOM),
                                       chip_detector_id='4321e7a4-38bf-44cc-8820-a33c9a0f66a0')

    analysis_service.add_chip_detector(name='Color segmentation',
                                       factory=ColorBasedChipDetector,
                                       chip_detector_id='17d6af81-1312-4b1b-a3b6-c8cf5c0c4c3a')

    # Register the pin detectors
    analysis_service.add_pin_detector(name="CV pipeline",
                                      factory=CvPipelinePinDetector,
                                      pin_detector_id='8956bee0-ee4e-497b-a471-97aa8724e6b4')

    analysis_service.add_pin_detector(name="Faster-RCNN",
                                      factory=lambda: TensorflowPinDetector(
                                          model=TensorflowPinDetector.FASTER_RCNN_IC_PINS),
                                      pin_detector_id='0b1aa126-d8db-4c3c-af7f-6910c7d3b1eb')

    # Create and configure the Flask application
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

    # Replace the default JSON encoder with a more feature-rich one
    app.json_encoder = EnhancedJsonEncoder

    # Register API blueprints (REST)
    app.register_blueprint(api_bp, url_prefix="/api")

    # Default route redirects to the API documentation
    app.add_url_rule('/', view_func=api_index)

    # Enable CORS
    CORS(app,
         resources={r"/api/*": {"origins": "*"}})

    # Inject the analyis service into the application
    app.analysis_service = analysis_service

    # Register a teardown handler to free the resources allocated
    # by the analysis service(s)
    atexit.register(analysis_service.release)

    return app
