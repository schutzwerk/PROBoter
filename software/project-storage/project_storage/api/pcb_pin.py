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

import numpy as np
from flask import request
from flask_restx import Namespace, Resource, fields

from project_storage.model import Pin

from .pcb import api
from .utils import array_field, NullableInteger, get_component_service, \
    get_pcb_service, get_network_service, get_pin_service


api = Namespace('Component pin',
                description='Pins that belong to a PCB component')


# Models
new_pin_model = api.model('NewPin', {
    'isVisible': fields.Boolean(required=False, default=True),
    'isTemporary': fields.Boolean(required=False, default=False),
    'networkId': NullableInteger(required=False, default=None),
    'componentId': NullableInteger(required=False, default=None),
    'center': array_field(shape=3, required=False),
    'name': fields.String(required=False, default=None)
})

pin_update_model = api.inherit('PinUpdate', new_pin_model, {})

pin_model = api.model('Pin', {
    'id': fields.Integer,
    'isVisible': fields.Boolean(attribute='is_visible'),
    'isTemporary': fields.Boolean(attribute='is_temporary'),
    'pcbId': fields.Integer(attribute='pcb_id'),
    'networkId': fields.Integer(attribute='network_id'),
    'componentId': fields.Integer(attribute='component_id'),
    'center': array_field(shape=3,
                          required=False,
                          attribute=lambda pin: pin.center.tolist()),
    'name': fields.String,
})


@api.route('/<int:pcb_id>/pin')
class PcbPinsResource(Resource):
    """
    Endpoints to fetch pins associated with a PCB and to create new pins
    """
    @staticmethod
    @api.marshal_with(pin_model, as_list=True)
    def get(pcb_id):
        """
        Retrieve and return all pins associated with this PCB
        """
        return get_pcb_service().get_pins(pcb_id)

    @staticmethod
    @api.marshal_with(pin_model)
    @api.expect(new_pin_model)
    @api.response(204, 'No PCB found with ID')
    def post(pcb_id):
        """
        Create a new pin associated with this PCB
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)
        pin = Pin(
            pcb_id=pcb_id,
            pcb=pcb
        )

        if 'isVisible' in request.json:
            pin.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            pin.is_temporary = request.json['isTemporary']
        if 'networkId' in request.json and request.json['networkId'] is not None:
            pin.network_id = request.json['networkId']
            pin.network = get_network_service().get_network_by_id(pin.network_id)
        if 'componentId' in request.json and request.json['componentId'] is not None:
            pin.component_id = request.json['componentId']
            pin.component = get_component_service().get_component_by_id(pin.component_id)
        if 'center' in request.json:
            pin.center = np.array(request.json['center'])
        if 'name' in request.json:
            pin.name = request.json['name']
        else:
            pin.name = "Pin"
        return get_pin_service().create_new_pin(pin)


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/pin/<int:pin_id>')
class PinResource(Resource):
    """
    Resource that provides access to retrieve and update a pin
    """
    log = logging.getLogger(__module__)

    @staticmethod
    @api.marshal_with(pin_model)
    @api.response(204, "No pin found with the given ID")
    def get(pcb_id: int, pin_id: int):
        """
        Returns the pin associated with the provided id
        """
        pin = get_pin_service().get_pin_by_id(pin_id)
        return pin

    @classmethod
    @api.expect(pin_update_model)
    @api.marshal_with(pin_model)
    @api.response(204, "No pin found with the given ID")
    def put(cls, pin_id: int, **_):
        """
        Updates an existing pin
        """
        cls.log.debug("Pin update request for pin %d", pin_id)
        pin: Pin = get_pin_service().get_pin_by_id(pin_id)

        if 'isVisible' in request.json:
            pin.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            pin.is_temporary = request.json['isTemporary']
        if 'networkId' in request.json:
            network_id = request.json['networkId']
            if network_id is None:
                pin.electrical_net = None
            else:
                pin.electrical_net = get_network_service().get_network_by_id(pin.network_id)
        if 'componentId' in request.json:
            component_id = request.json['componentId']
            if component_id is None:
                pin.component = None
            else:
                pin.component = get_component_service().get_component_by_id(component_id)
        if 'center' in request.json:
            pin.center = np.array(request.json['center'])
        if 'name' in request.json:
            pin.name = request.json['name']

        cls.log.debug("Updating pin")
        pin = get_pin_service().update_pin(pin)
        cls.log.debug("Successfully updated pin: %s", pin)

        return pin

    @staticmethod
    @api.response(204, "No pin found with the given ID")
    def delete(pcb_id: int, pin_id: int):
        """
        Delete an existing pin
        """
        get_pin_service().delete_pin_by_id(pin_id)
