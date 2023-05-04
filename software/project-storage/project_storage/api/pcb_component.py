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

from project_storage.model import PcbComponent, PcbComponentPackage

from .utils import array_field, get_pcb_service, get_component_service


api = Namespace('PCB component', description='PCB components like ICs, etc.')


# Models
new_component_model = api.model('NewComponent', {
    'isVisible': fields.Boolean(required=False),
    'isTemporary': fields.Boolean(required=False),
    'marking': fields.String(required=False),
    'vendor': fields.String(required=False),
    'contour': array_field(shape=(-1, 3), required=False),
    'package': fields. String(required=False, enum=[v.name for v in PcbComponentPackage]),
    'name': fields.String(required=False)
})

component_update_model = api.inherit(
    'ComponentUpdate', new_component_model, {})

component_model = api.model('Component', {
    'id': fields.Integer,
    'isVisible': fields.Boolean(attribute='is_visible'),
    'isTemporary': fields.Boolean(attribute='is_temporary'),
    'marking': fields.String,
    'vendor': fields.String,
    'package': fields.String(attribute=lambda comp: comp.package.value if comp.package else None),
    'name': fields.String,
    'pcbId': fields.Integer(attribute='pcb_id'),
    'contour': array_field(shape=(-1, 3),
                           attribute=lambda comp: comp.contour.tolist())
})


@api.route('/<int:pcb_id>/component')
class PcbComponentsResource(Resource):
    """
    Resource that provides access to a PCB's associated components
    """
    @staticmethod
    @api.marshal_with(component_model, as_list=True)
    def get(pcb_id):
        """
        Retrieve and return all components associated with this pcb
        """
        return get_pcb_service().get_components(pcb_id)

    @staticmethod
    @api.marshal_with(component_model)
    @api.expect(new_component_model)
    @api.response(204, 'No PCB found with ID')
    def post(pcb_id):
        """
        Create a new PCB Component associated with this PCB
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)
        component = PcbComponent(
            pcb_id=pcb_id,
            pcb=pcb
        )
        if 'isVisible' in request.json:
            component.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            component.is_temporary = request.json['isTemporary']
        if 'marking' in request.json:
            component.marking = request.json['marking']
        if 'vendor' in request.json:
            component.vendor = request.json['vendor']
        if 'contour' in request.json:
            component.contour = np.array(request.json['contour'])
        if 'package' in request.json:
            component.package = PcbComponentPackage(request.json['package'])
        if 'name' in request.json:
            component.name = request.json['name']
        return get_component_service().create_new_component(component)


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/component/<int:component_id>')
class PcbComponentResource(Resource):
    """
    Resource that provides access to retrieve and update a component
    """
    @staticmethod
    @api.marshal_with(component_model)
    @api.response(204, "No component found with the given ID")
    def get(pcb_id: int, component_id: int):
        """
        Return the component associated with the provided id
        """
        component = get_component_service().get_component_by_id(component_id)
        return component

    @staticmethod
    @api.expect(component_update_model)
    @api.marshal_with(component_model)
    @api.response(204, "No component found with the given ID")
    def put(pcb_id: int, component_id: int):
        """
        Update an existing component
        """
        component = get_component_service().get_component_by_id(component_id)
        if 'marking' in request.json:
            component.marking = request.json['marking']
        if 'isVisible' in request.json:
            component.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            component.is_temporary = request.json['isTemporary']
        if 'vendor' in request.json:
            component.vendor = request.json['vendor']
        if 'contour' in request.json:
            component.contour = np.array(request.json['contour'])
        if 'package' in request.json:
            component.package = PcbComponentPackage(request.json['package'])
        if 'name' in request.json:
            component.name = request.json['name']
        component = get_component_service().update_component(component)
        return component

    @staticmethod
    @api.response(204, "No component found with the given ID")
    def delete(pcb_id: int, component_id: int):
        """
        Delete an existing PCB component
        """
        get_component_service().delete_component_by_id(component_id)
