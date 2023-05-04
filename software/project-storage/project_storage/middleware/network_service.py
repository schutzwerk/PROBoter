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
from typing import Iterable

from project_storage.model import db, ElectricalNet, Pin


class NetworkService:
    """
    Service that offers operations to query or modify identified Networks
    """

    log = logging.getLogger(__name__)

    @classmethod
    def get_networks(cls) -> Iterable[ElectricalNet]:
        """
        Fetch a list of all stored Networks

        :return: List of all stored Networks
        :rtype: Iterable[ElectricalNet]
        """
        return ElectricalNet.query.all()

    @classmethod
    def get_pins(cls, network_id: int) -> Iterable[Pin]:
        """
        Fetch a list of all pins associated with the given network id

        :param network_id: The id of the network whose pins are to be retrieved
        :type network_id: int
        :return: List of associated pins
        :rtype: Iterable[Pin]
        """
        return Pin.query.filter_by(network_id=network_id).all()

    @classmethod
    def get_network_by_id(cls, network_id: int) -> ElectricalNet:
        """
        Fetch a single, stored Network by it's unique ID

        :param network_id: ID of the Network to fetch
        :type network_id: int
        :return: The stored Network
        :rtype: ElectricalNet
        """
        return ElectricalNet.query.filter_by(id=network_id).one()

    @classmethod
    def create_new_network(cls, network: ElectricalNet) -> ElectricalNet:
        """
        Create a new network instance

        :param network: The network instance with the desired attributes
        :type network: ElectricalNet
        :return: The stored Network
        :rtype: ElectricalNet
        """
        cls.log.info("Creating new Network: %s", network)

        db.session.add(network)
        db.session.commit()
        return network

    @classmethod
    def update_network(cls, network: ElectricalNet) -> ElectricalNet:
        """
        Update an existing Network

        :param network: Network to update
        :type network: ElectricalNet
        :return: The updated Network
        :rtype: ElectricalNet
        """
        if network.id is None:
            msg = "Network has no ID"
            cls.log.error(msg)
            raise Exception(msg)

        cls.log.info("Updating network with ID %d: %s", network.id, network)
        db.session.add(network)
        db.session.commit()

        return network

    @classmethod
    def delete_network_by_id(cls, network_id: int) -> None:
        """
        Permanently delete a Network

        :param network_id: Unique identifier of the Network to delete
        :type network_id: int
        """
        network = ElectricalNet.query.filter_by(id=network_id).one()

        cls.log.info("Deleting Network with ID %d", network_id)
        db.session.delete(network)
        db.session.commit()
