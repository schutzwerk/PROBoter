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
from typing import Optional
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from proboter.fields import NumpyArray

from .config import StorageBackendConfig


# pylint: disable=too-many-instance-attributes
@dataclass
class Pin:
    """
    A single pin
    """
    # Unique ID of the pin
    id: Optional[int] = None
    # Name of the pin
    name: str = ""
    # Whether the pin is visible
    is_visible: bool = True
    # Whether the pin is only temporary
    is_temporary: bool = False
    # ID of the PCB the pin belongs to
    pcb_id: Optional[int] = None
    # ID of the network the pin belongs to
    network_id: Optional[int] = None
    # ID of the component the pin belongs to
    component_id: Optional[int] = None
    # Pin center as 3D vector
    center: NumpyArray = Field(np_shape=3)

    log = logging.getLogger(__module__)

    @classmethod
    async def get_by_id(cls, pcb_id: int, pin_id: int) -> "Pin":
        """
        Get a single pin by its ID

        :param pcb_id: ID of the PCB the pin belongs to
        :type pcb_id: int
        :param pin_id: ID of the pin
        :type pin_id: int
        :return: Pin with the given ID if any
        :rtype: Pin
        """
        cls.log.info("Loading pin with ID %d", pin_id)
        async with StorageBackendConfig.session() as session:
            api_url = StorageBackendConfig.api_url(
                f'/pcb/{pcb_id}/pin/{pin_id}')
            async with session.get(api_url) as resp:
                response_data = await resp.json()
                return Pin(
                    id=response_data["id"],
                    name=response_data["name"],
                    is_visible=response_data["isVisible"],
                    is_temporary=response_data["isTemporary"],
                    pcb_id=response_data["pcbId"],
                    network_id=response_data["networkId"],
                    component_id=response_data["componentId"],
                    center=np.array(response_data["center"]))
