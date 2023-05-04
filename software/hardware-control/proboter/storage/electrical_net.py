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

import logging
from typing import Optional, List
from dataclasses import dataclass

from pydantic import Field

from .config import StorageBackendConfig


@dataclass
class ElectricalNet:
    """
    An electrical network
    """
    # Unique ID of the electrical network
    id: Optional[int] = None
    # Name of the net
    name: str = ""
    # Whether the net is visible
    is_visible: bool = True
    # Whether the net is only temporary
    is_temporary: bool = False
    # ID of the PCB the net belongs to
    pcb_id: Optional[int] = None
    # List of pins / pads that belong to the electrical net
    pin_ids: List[int] = Field(default_factory=list)

    log = logging.getLogger(__module__)

    @classmethod
    async def get_by_id(cls, pcb_id: int, net_id: int) -> "ElectricalNet":
        """
        Get a single electrical net by its ID

        :param pcb_id: ID of the PCB the net belongs to
        :type pcb_id: int
        :param net_id: ID of the net
        :type net_id: int
        :return: Electrical net with the given ID if any
        :rtype: ElectricalNet
        """
        cls.log.info("Loading electrical net with ID %d", net_id)
        async with StorageBackendConfig.session() as session:
            api_url = StorageBackendConfig.api_url(
                f'/pcb/{pcb_id}/network/{net_id}')
            async with session.get(api_url) as resp:
                response_data = await resp.json()
                return cls._from_json(response_data)

    @classmethod
    async def get_all_of_pcb(cls, pcb_id: int) -> List["ElectricalNet"]:
        """
        Get all electrical nets defined on a PCB

        :param pcb_id: ID of the PCB the net belongs to
        :type pcb_id: int
        :return: List of electrical nets defined on the PCB
        :rtype: List[ElectricalNet]
        """
        cls.log.info("Loading electrical nets for PCB  ID %d", pcb_id)
        async with StorageBackendConfig.session() as session:
            api_url = StorageBackendConfig.api_url(
                f'/pcb/{pcb_id}/network')
            async with session.get(api_url) as resp:
                response_data = await resp.json()
                return [cls._from_json(net_data)
                        for net_data in response_data]

    @staticmethod
    def _from_json(data: dict) -> "ElectricalNet":
        """
        Parse an electrical net definition from
        the storage JSON result
        """
        return ElectricalNet(
            id=data["id"],
            name=data["name"],
            is_visible=data["isVisible"],
            is_temporary=data["isTemporary"],
            pcb_id=data["pcbId"],
            pin_ids=data["pinIds"])
