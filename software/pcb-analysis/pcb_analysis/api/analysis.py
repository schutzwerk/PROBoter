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

import logging
from io import BytesIO

import cv2
import numpy as np
from werkzeug.datastructures import FileStorage
from flask import abort, current_app, request, send_file
from flask_restx import Namespace, Resource, fields, marshal

from pcb_analysis.visual_analysis import AnalysisService
from pcb_analysis.utils import draw_chip_detections, draw_pin_detections


# Endpoint description
api = Namespace('analysis',
                path='/analysis',
                description='PCB image analysis operations')


# Models
pin_detection_model = api.model('PinDetection', {
    'id': fields.String(attribute='pin_id',
                        example='fbb400c8-cbc4-4e11-b75a-ac788b230c95'),
    'confidence': fields.Float,
    'center': fields.List(fields.Float,
                          attribute=lambda pd: pd.center.tolist(),
                          example=[0, 0])
})

chip_detection_model = api.model('ChipDetetion', {
    'id': fields.String(attribute='chip_id',
                        example='fbb400c8-cbc4-4e11-b75a-ac788b239c95'),
    'package': fields.String(attribute=lambda chip: str(chip.package.value),
                             example='BGA'),
    'confidence': fields.Float,
    'vendor': fields.String,
    'marking': fields.String,
    'contour': fields.List(fields.List(fields.Float),
                           attribute=lambda cd: cd.bbox.tolist(),
                           example=[[0, 0], [1, 0], [1, 1], [1, 0]]),
    'pins': fields.Nested(pin_detection_model)
})

analysis_results_model = api.model('AnalysisResults', {
    'components': fields.List(fields.Nested(chip_detection_model), attribute="chips"),
    'pads': fields.List(fields.Nested(pin_detection_model))
})


# Request parser
analysis_parser = api.parser()
analysis_parser.add_argument('pcb-image', location='files', dest='pcb_image',
                             type=FileStorage, required=True,
                             help="PCB image to analyse")
analysis_parser.add_argument('chip-detector', type=str, dest='chip_detector_id',
                             default="ded48437-36bc-4116-a374-1aaa6b0d7681",
                             location='form', required=True,
                             help="Unique identifier of the chip detector used for the analysis")
analysis_parser.add_argument('pin-detector', type=str, dest='pin_detector_id',
                             location='form', required=False,
                             default=None,
                             help="Unique identifier of the pin detector used for the analysis")


@api.route('')
@api.expect(analysis_parser)
class PcbImageAnalysisResource(Resource):
    """
    Resource that exposes PCB image analysis functionality
    """
    log = logging.getLogger(__name__)

    @api.produces(['image/png', 'application/json'])
    @api.response(200, 'Success', analysis_results_model)
    def post(self):
        """
        Analyse a single PCB image
        """
        self.log.info("Analysis request from %s", request.remote_addr)

        # Parse the request parameters
        args = analysis_parser.parse_args()

        # Parse the PCB image data
        try:
            nparr = np.frombuffer(args.pcb_image.read(), np.uint8)
            pcb_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            if pcb_image is None:
                abort(400, "Invalid or malformed PCB image")
        except cv2.error:
            abort(400, "Invalid or malformed PCB image")

        # Fetch the selected detectors
        analysis_service: AnalysisService = current_app.analysis_service

        chip_detector = analysis_service.get_chip_detector_by_id(
            args.chip_detector_id)
        if chip_detector is None:
            abort(400, "Unknown chip detector")

        pin_detector = None
        if args.pin_detector_id is not None:
            pin_detector = analysis_service.get_pin_detector_by_id(
                args.pin_detector_id)
            if pin_detector is None:
                abort(400, "Unknown pin detector")

        # Perform the PCB image analysis
        res = analysis_service.analyse_pcb_image(pcb_image,
                                                 chip_detector,
                                                 pin_detector)

        if request.headers.get('Accept', None) == 'image/png':
            # Draw the chip detection results
            line_width = max(1, int(0.002 * np.max(pcb_image.shape)))
            result_img = draw_chip_detections(pcb_image, res.chips,
                                              line_width=line_width)

            # Draw the pin detection results
            pins = list(res.pads)
            for chip in res.chips:
                pins += chip.pins
            result_img = draw_pin_detections(pcb_image, pins,
                                             marker_size=max(
                                                 1, int(0.015 * np.max(pcb_image.shape))),
                                             marker_thickness=max(
                                                 1, int(0.001 * np.max(pcb_image.shape))),
                                             draw_pin_contours=False)

            # Convert the image to an encoded byte stream
            _, encoded_img = cv2.imencode('.png', result_img)
            img_io = BytesIO()
            img_io.write(encoded_img)
            img_io.seek(0)

            # Send the image
            return send_file(img_io,
                             mimetype='image/png',
                             download_name='result.png')

        return marshal(res, analysis_results_model)
