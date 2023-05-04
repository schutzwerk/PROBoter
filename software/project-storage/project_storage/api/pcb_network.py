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

from flask import request
from flask_restx import Namespace, Resource, fields

from project_storage.model import ElectricalNet

from .utils import array_field, get_network_service, get_pcb_service, \
    get_pin_service


api = Namespace('Electrical net',
                description='Electrical networks identified on a PCB')


# Models
new_network_model = api.model('Network', {
    'name': fields.String(required=False),
    'isVisible': fields.Boolean(required=False),
    'isTemporary': fields.Boolean(required=False),
    'pinIds': array_field(
        shape=-1,
        attribute=lambda network: [pin.id for pin in network.pins] \
                                  if network is not None else [],
        required=False
    )
})

network_update_model = api.inherit('NetworkUpdate', new_network_model, {
})

network_model = api.model('Network', {
    'id': fields.Integer,
    'name': fields.String(),
    'pcbId': fields.Integer(attribute="pcb_id"),
    'isVisible': fields.Boolean(attribute="is_visible"),
    'isTemporary': fields.Boolean(attribute="is_temporary"),
    'pinIds': array_field(
        shape=-1,
        attribute=lambda network: [
            pin.id for pin in network.pins] if network is not None else []
    )
})


@api.route('/<int:pcb_id>/network')
class PcbNetworksResource(Resource):
    """
    Resource that provides access to a PCB's associated networks
    """
    @staticmethod
    @api.marshal_with(network_model, as_list=True)
    def get(pcb_id):
        """
        Retrieve and return all networks associated with this pcb
        """
        networks = get_pcb_service().get_networks(pcb_id)
        return networks

    @staticmethod
    @api.marshal_with(network_model)
    @api.expect(new_network_model)
    @api.response(204, 'No PCB found with ID')
    def post(pcb_id):
        """
        Create a new Network associated with this PCB
        """
        pcb = get_pcb_service().get_pcb_by_id(pcb_id)
        network = ElectricalNet(
            pcb_id=pcb_id,
            pcb=pcb
        )
        if 'name' in request.json:
            network.name = request.json['name']
        if 'isVisible' in request.json:
            network.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            network.is_temporary = request.json['isTemporary']
        network = get_network_service().create_new_network(network)
        if 'pinIds' in request.json:
            for pin_id in request.json['pinIds']:
                pin = get_pin_service().get_pin_by_id(pin_id)
                if pin.pcb_id != pcb.id:
                    api.abort(204, 'Pin id is not associated with this pcb')
                pin.network = network
                pin.network_id = network.id
        return get_network_service().update_network(network)


# 'unused-argument' is disabled as the path
# parameters are required by flask(-restx) here
# pylint: disable=locally-disabled, unused-argument
@api.route('/<int:pcb_id>/network/<int:network_id>')
class NetworkResource(Resource):
    """
    Resource that provides access to retrieve and update a network
    """
    @staticmethod
    @api.marshal_with(network_model)
    @api.response(204, "No network found with the given ID")
    def get(pcb_id: int, network_id: int):
        """
        Returns the network associated with the provided id
        """
        network = get_network_service().get_network_by_id(network_id)
        return network

    @staticmethod
    @api.expect(network_update_model)
    @api.marshal_with(network_model)
    @api.response(204, "No network found with the given ID")
    def put(pcb_id: int, network_id: int):
        """
        Updates an existing network
        """
        network = get_network_service().get_network_by_id(network_id)
        if 'name' in request.json:
            network.name = request.json['name']
        if 'isVisible' in request.json:
            network.is_visible = request.json['isVisible']
        if 'isTemporary' in request.json:
            network.is_temporary = request.json['isTemporary']
        if 'pinIds' in request.json:
            network_pins = get_network_service().get_pins(network_id)
            for pin in network_pins:
                if pin.id not in request.json['pinIds']:
                    pin.network_id = None
                    pin.network = None
            for pin_id in request.json['pinIds']:
                pin = get_pin_service().get_pin_by_id(pin_id)
                pin.network = network
                pin.network_id = network_id
        network = get_network_service().update_network(network)
        return network

    @staticmethod
    @api.response(204, "No network found with the given ID")
    def delete(pcb_id: int, network_id: int):
        """
        Delete an existing electrical network
        """
        get_network_service().delete_network_by_id(network_id)
