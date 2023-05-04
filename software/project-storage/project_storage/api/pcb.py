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

import numpy as np
from flask import request
from flask_restx import Namespace, Resource, fields

from .utils import get_pcb_service, send_image


api = Namespace('PCB', description='Analysed PCBs')

# Models
pcb_new_model = api.model('PcbNew', {
    'name': fields.String(required=False, default=""),
    'description': fields.String(required=False, default=""),
    'thickness': fields.Float(required=True)
})

pcb_update_model = api.inherit('PcbUpdate', pcb_new_model, {})

pcb_model = api.inherit('Pcb', pcb_new_model, {
    'id': fields.Integer,
    'numScans': fields.Integer(attribute=lambda pcb: len(pcb.scans)),
    'numComponents': fields.Integer(attribute=lambda pcb: len(pcb.components)),
    'numNetworks': fields.Integer(attribute=lambda pcb: len(pcb.networks))
})


@api.route('')
class PcbListResource(Resource):
    """
    Resource that provides a list of all analysed PCBs and
    also offers the possibility to create new PCBs
    """
    @staticmethod
    @api.marshal_with(pcb_model, as_list=True)
    def get():
        """
        Return all analysed PCBs
        """
        return get_pcb_service().get_pcbs()

    @staticmethod
    @api.expect(pcb_new_model)
    @api.marshal_with(pcb_model)
    def post():
        """
        Create a new PCB
        """
        name = ""
        description = ""
        thickness = request.json['thickness']
        if 'name' in request.json:
            name = request.json['name']
        if 'description' in request.json:
            description = request.json['description']
        return get_pcb_service().create_pcb(name, description, thickness)


@api.route('/<int:pcb_id>')
class PcbResource(Resource):
    """
    Resource that represents a single PCB
    """
    @staticmethod
    @api.marshal_with(pcb_model)
    @api.response(204, 'No PCB found with ID')
    def get(pcb_id):
        """
        Return a single PCB
        """
        return get_pcb_service().get_pcb_by_id(pcb_id)

    @staticmethod
    @api.marshal_with(pcb_model)
    @api.expect(pcb_update_model)
    @api.response(204, 'No PCB found with ID')
    def put(pcb_id):
        """
        Update an existing PCB
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)
        if 'name' in request.json:
            pcb.name = request.json['name']
        if 'description' in request.json:
            pcb.description = request.json['description']
        return get_pcb_service().update_pcb(pcb)

    @staticmethod
    @api.response(204, 'No PCB found with ID')
    def delete(pcb_id):
        """
        Delete a PCB an all it's attached data
        """
        get_pcb_service().delete_pcb_by_id(pcb_id)


@api.route('/<int:pcb_id>/preview')
class PcbPreviewResource(Resource):
    """
    Resource that provides a preview image of the pcb
    """
    @staticmethod
    @api.response(204, 'No PCB found with ID')
    def get(pcb_id):
        """
        Return a preview image of a scan associate with this pcb
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)
        img: np.ndarray = pcb.preview_image_data
        return send_image(img)
