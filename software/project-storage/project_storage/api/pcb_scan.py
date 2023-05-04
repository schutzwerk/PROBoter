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

import base64
import logging
from io import BytesIO

import cv2
import numpy as np
from flask import request, make_response, send_file
from flask_restx import Namespace, Resource, fields
from werkzeug.datastructures import FileStorage

from project_storage.model import PcbScan, PcbScanImage

from .pcb import api
from .utils import get_scan_service, get_pcb_service, send_image, array_field


api = Namespace('PCB scan',
                description='PCB scan / image data')

# Models
pcb_scan_new_model = api.model('PcbScanNew', {
    'name': fields.String,
    'isVisible': fields.Boolean(attribute='is_visible'),
    'xMin': fields.Float(attribute='x_min'),
    'xMax': fields.Float(attribute='x_max'),
    'yMin': fields.Float(attribute='y_min'),
    'yMax': fields.Float(attribute='y_max'),
    'zOffset': fields.Float(attribute='z_offset'),
})

pcb_scan_model = api.inherit('PcbScan', pcb_scan_new_model, {
    'id': fields.Integer,
    'numImages': fields.Integer(attribute=lambda scan: len(scan.images)),
    'scanImages': fields.List(fields.Integer,
                              attribute=lambda scan: [image.id for image in scan.images]),
    'pcbId': fields.Integer(attribute='pcb_id')
})

pcb_scan_image_new_model = api.model('PcbScanImageNew', {
    'image': fields.String,
    'cameraMatrix': array_field(shape=(3, 3),
                                required=True,
                                attribute=lambda scan_image: scan_image.camera_matrix.tolist()),
    'tmat': array_field(shape=(4, 4),
                        required=True,
                        attribute=lambda scan_image: scan_image.tmat.tolist()),
    'zOffset': fields.Float(attribute='z_offset'),
})

pcb_scan_image_model = api.inherit('PcbScanImage', pcb_scan_image_new_model, {
    'id': fields.Integer,
    'imageWidth': fields.Integer(attribute='image_width'),
    'imageHeight': fields.Integer(attribute='image_height'),
    'imageChannels': fields.Integer(attribute='image_channels')
})

# Request parser
scan_import_parser = api.parser()
scan_import_parser.add_argument('scan-file', location='files', dest='scan_file',
                                type=FileStorage, required=True,
                                help="PCB scan file")


@api.route('/<int:pcb_id>/scan')
class PcbScansResource(Resource):
    """
    Provides access to get scans
    """

    @staticmethod
    @api.response(204, 'No PCB found with ID')
    @api.marshal_with(pcb_scan_model, as_list=True)
    def get(pcb_id):
        """
        Return a list of scan ids associated with this pcb
        """
        return get_scan_service().get_pcb_scans_by_pcb_id(pcb_id)

    @staticmethod
    @api.expect(pcb_scan_new_model)
    @api.marshal_with(pcb_scan_model)
    @api.response(204, 'No PCB scan found with ID')
    def post(pcb_id):
        """
        Create a new PCB scan
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)

        scan = PcbScan(
            is_visible=request.json['isVisible'],
            name=request.json['name'],
            x_min=request.json['xMin'],
            x_max=request.json['xMax'],
            y_min=request.json['yMin'],
            y_max=request.json['yMax'],
            z_offset=request.json['zOffset'],
            pcb=pcb
        )

        return get_scan_service().create_or_update_scan(scan)


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/scan/<int:scan_id>')
class PcbScanResource(Resource):
    """
    Resource that provides access to individual PCB scans
    """
    @staticmethod
    @api.marshal_with(pcb_scan_model)
    @api.response(204, 'No PCB scan found with ID')
    def get(pcb_id, scan_id):
        """
        Return a single PCB scan. The image data is not included but
        can be requested from the `scan/<scan_id>/image` endpoint.
        """
        return get_scan_service().get_pcb_scan_by_id(scan_id)

    @staticmethod
    @api.response(204, 'No PCB found with ID')
    def delete(pcb_id, scan_id):
        """
        Delete a scan
        """
        get_scan_service().delete_pcb_scan_by_id(scan_id)


@api.route('/<int:pcb_id>/scan/import')
class ScanImportResource(Resource):
    """
    Resource that allows the import of a previously exported scan
    """
    log = logging.getLogger(__module__)

    @classmethod
    @api.expect(scan_import_parser)
    @api.marshal_with(pcb_scan_model)
    @api.response(415, 'Invalid MIME type of PCB scan file')
    def post(cls, pcb_id):
        """
        Import a previously exported PCB scan
        """
        # Parse the request parameters
        args = scan_import_parser.parse_args()
        cls.log.info("Received scan import request for file '%s' from %s",
                     args.scan_file.filename, request.remote_addr)

        # Basic MIME type checking
        if args.scan_file.content_type != 'application/zip':
            api.abort(415, 'Invalid MIME type of PCB scan file')

        # Import the file
        return get_scan_service().import_pcb_scan_from_file(pcb_id, args.scan_file)


@api.route('/<int:pcb_id>/scan/<int:scan_id>/export')
class PcbScanExportResource(Resource):
    """
    Resource that allows the export of a single scan
    """
    @staticmethod
    @api.produces(['application/zip'])
    def get(scan_id: int, pcb_id: int):
        """
        Export a PCB scan
        """
        file_io = BytesIO()
        get_scan_service().export_pcb_scan_to_file(scan_id, file_io)
        file_io.seek(0)
        # Send the file
        response = make_response(send_file(file_io,
                                           mimetype='application/zip',
                                           download_name=f'scan_{scan_id}.zip'))
        response.headers['Cache-Control'] = 'no-cache'
        return response


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/scan/<int:scan_id>/image')
class PcbScanImageResource(Resource):
    """
    Resource that provides access to the (stitched) scan image
    """
    @staticmethod
    @api.produces(['image/png'])
    def get(pcb_id, scan_id):
        """
        Return the (merged) image of a PCB scan
        """
        img = get_scan_service().get_merged_pcb_scan_image(scan_id,
                                                           resolution=0.1)
        return send_image(img)

    @staticmethod
    @api.expect(pcb_scan_image_new_model)
    @api.marshal_with(pcb_scan_image_model)
    @api.response(204, 'No PCB scan found with ID')
    def post(pcb_id, scan_id):
        """
        Create a new PCB scan image
        """
        scan = get_scan_service().get_pcb_scan_by_id(scan_id)

        # TODO Add handling of invalid image data
        raw_image = base64.b64decode(request.json['image'])
        nparr = np.fromstring(raw_image, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        scan_image = PcbScanImage(
            image_data=image,
            image_width=image.shape[1],
            image_height=image.shape[0],
            image_channels=image.shape[2],
            camera_matrix=np.array(
                request.json['cameraMatrix'],
                dtype=np.float32),
            tmat=np.array(request.json['tmat'], dtype=np.float32),
            z_offset=request.json['zOffset'],
            scan=scan
        )

        return get_scan_service().create_or_update_scan_image(scan_image)


@api.route('/<int:pcb_id>/scan/<int:scan_id>/image/<int:scan_image_id>')
class PcbScanImageDataResource(Resource):
    """
    Resource that provides access a single scan image
    """
    @staticmethod
    @api.produces(['image/png'])
    def get(scan_id, scan_image_id, **_):
        """
        Return the image of a single PCB scan image
        """
        img = get_scan_service().get_individual_pcb_scan_image(scan_id,
                                                               scan_image_id)
        return send_image(img)


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/scan/<int:scan_id>/preview')
class PcbScanPreviewResource(Resource):
    """
    Resource that provides a preview image of the pcb
    """
    @staticmethod
    @api.response(204, 'No PCB found with ID')
    def get(pcb_id, scan_id):
        """
        Return a preview image of a scan associate with this pcb
        """
        preview = get_scan_service().get_pcb_scan_preview(scan_id)
        return send_image(preview)
