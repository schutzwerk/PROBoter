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

import numpy as np

from project_storage.model import db, Pcb, PcbComponent, Pin, ElectricalNet


class PcbService:
    """
    Service that offers operations to query or modify analysed PCBs
    """

    log = logging.getLogger(__name__)

    @classmethod
    def get_pcbs(cls) -> Iterable[Pcb]:
        """
        Fetch a list of all stored PCBs

        :return: List of all stored PCBs
        :rtype: Iterable[Pcb]
        """
        return Pcb.query.all()

    @classmethod
    def get_pcb_by_id(cls, pcb_id: int) -> Pcb:
        """
        Fetch a single, stored PCB by it's unique ID

        :param pcb_id: ID of the PCB to fetch
        :type pcb_id: int
        :return: The stored PCB
        :rtype: Pcb
        """
        return Pcb.query.filter_by(id=pcb_id).one()

    @classmethod
    def create_pcb(cls, name: str, description: str, thickness: float) -> Pcb:
        """
        Create a new PCB

        :param name: Display name of the PCB
        :type name: str
        :param description: Detailed description of the PCB
        :type description: str
        :param thickness: PCB thickness in mm
        :type thickness: float
        :return: The newly created PCB
        :rtype: Pcb
        """
        pcb = Pcb(name=name,
                  description=description,
                  thickness=thickness)

        # Create a default preview image
        width = 200
        height = 200
        pcb.preview_image_data = np.zeros((height, width, 3), dtype=np.uint8)
        pcb.preview_image_width = width
        pcb.preview_image_width = height

        cls.log.info("Creating new PCB: %s", pcb)

        db.session.add(pcb)
        db.session.commit()

        return pcb

    @classmethod
    def update_pcb(cls, pcb: Pcb) -> Pcb:
        """
        Update an existing PCB

        :param pcb: PCB to update
        :type pcb: Pcb
        :return: The updated PCB
        :rtype: Pcb
        """
        if pcb.id is None:
            msg = "PCB has no ID"
            cls.log.error(msg)
            raise Exception(msg)

        cls.log.info("Updating PCB with ID %d: %s", pcb.id, pcb)
        db.session.add(pcb)
        db.session.commit()

        return pcb

    @classmethod
    def update_pcb_preview_image(cls, pcb: Pcb,
                                 preview_image: np.ndarray) -> Pcb:
        """
        Update the preview image of a PCB

        :param pcb: PCB to update
        :type pcb: Pcb
        :param preview_image: New preview image of the PCB
        :type preview_image: np.ndarray
        :return: Updated PCB
        :rtype: Pcb
        """
        cls.log.info("Updating preview image of PCB with ID: %d", pcb.id)
        pcb.preview_image_data = preview_image
        pcb.preview_image_width = preview_image.shape[1]
        pcb.preview_image_height = preview_image.shape[0]

        db.session.add(pcb)
        db.session.commit()

        return pcb

    @classmethod
    def delete_pcb_by_id(cls, pcb_id: int) -> None:
        """
        Permanently delete a PCB

        :param pcb_id: Unique identifier of the PCB to delete
        :type pcb_id: int
        """
        pcb = Pcb.query.filter_by(id=pcb_id).one()

        cls.log.info("Deleting PCB with ID %d", pcb_id)
        db.session.delete(pcb)
        db.session.commit()

    @classmethod
    def get_components(cls, pcb_id: int) -> Iterable[PcbComponent]:
        """
        Return a list of all chip components associated with the pcb with the given id

        :param pcb_id: Unique identifier of the PCB whose components to get
        :type pcb_id: int
        :return: List of components
        :rtype: Iterable[PcbComponent]
        """
        return PcbComponent.query.filter_by(pcb_id=pcb_id).all()

    @classmethod
    def get_pins(cls, pcb_id: int) -> Iterable[Pin]:
        """
        Return a list of all pins associated with the pcb with the given id

        :param pcb_id: Unique identifier of the PCB whose pins to get
        :type pcb_id: int
        :return: List of pins
        :rtype: Iterable[Pin]
        """
        return Pin.query.filter_by(pcb_id=pcb_id).all()

    @classmethod
    def get_networks(cls, pcb_id: int) -> Iterable[ElectricalNet]:
        """
        Return a list of all networks associated with the pcb with the given id

        :param pcb_id: Unique identifier of the PCB to delete
        :type pcb_id: int
        :return: List of networks
        :rtype: Iterable[ElectricalNet]
        """
        networks = ElectricalNet.query.filter_by(pcb_id=pcb_id).all()
        return networks
