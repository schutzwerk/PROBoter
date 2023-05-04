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

import base64
import logging
from dataclasses import dataclass
from typing import Optional

import cv2
from pydantic import Field

from proboter.fields import NumpyArray

from .config import StorageBackendConfig


# pylint: disable=too-many-instance-attributes
@dataclass
class PcbScan:
    """
    Complete PCB scan
    """
    id: Optional[int] = None
    # Whether the scan is visible
    is_visible: bool = True
    # User-defined name of the scan
    name: str = ''
    # Lower boundary in X direction of the scan area
    x_min: float = 0.0
    # Upper boundary in X direction of the scan area
    x_max: float = 0.0
    # Lower boundary in Y direction of the scan area
    y_min: float = 0.0
    # Upper boundary in Y direction of the scan area
    y_max: float = 0.0
    # Offset in Z direction in mm from the reference XY plane
    z_offset: float = 0.0
    # ID of the PCB the scan belongs to
    pcb_id: Optional[int] = None

    log = logging.getLogger(__module__)

    async def save(self) -> None:
        """
        Create or update the PCB scan in the storage service
        """
        json_data = {
            'name': self.name,
            'isVisible': self.is_visible,
            'xMin': float(self.x_min),
            'xMax': float(self.x_max),
            'yMin': float(self.y_min),
            'yMax': float(self.y_max),
            'zOffset': float(self.z_offset)
        }

        async with StorageBackendConfig.session() as session:
            if self.id is None:
                self.log.info("Create PCB scan")
                api_url = StorageBackendConfig.api_url(
                    f'/pcb/{self.pcb_id}/scan')
                async with session.post(api_url, json=json_data) as resp:
                    response_data = await resp.json()
                    self.id = response_data["id"]
            else:
                self.log.info("Update PCB scan")
                raise NotImplementedError()


@dataclass
class PcbScanImage:
    """
    Single PCB scan image
    """
    # PCB scan the image belongs to
    scan: Optional[PcbScan] = None
    # Unique identifier of the scan image
    id: Optional[int] = None
    # Scan image data
    image: NumpyArray = Field(np_shape=(-1, -1, -1))
    # Camera matrix containing the instrinsic parameters of the camera
    # system that created the image as (3x3) numpy array
    camera_matrix: NumpyArray = Field(np_shape=(3, 3))
    # The transformation matrix of the camera system at the time of the image
    # capture as (4x4) numpy array
    tmat: NumpyArray = Field(np_shape=(4, 4))
    # Offset in Z direction in mm from the reference XY plane
    z_offset: float = 0.0

    log = logging.getLogger(__module__)

    async def save(self) -> None:
        """
        Create or update the PCB scan in the storage service
        """
        _, image_encoded = cv2.imencode(".png", self.image)
        image_base64 = base64.b64encode(
            image_encoded.tobytes()).decode("ascii")

        json_data = {
            'image': image_base64,
            'cameraMatrix': self.camera_matrix.tolist(),
            'tmat': self.tmat.tolist(),
            'zOffset': self.z_offset
        }

        async with StorageBackendConfig.session() as session:
            if self.id is None:
                self.log.info("Create PCB scan image")
                api_url = StorageBackendConfig.api_url(
                    f'/pcb/{self.scan.pcb_id}/scan/{self.scan.id}/image')
                async with session.post(api_url,
                                        json=json_data) as resp:
                    response_data = await resp.json()
                    self.id = response_data["id"]
            else:
                self.log.info("Update PCB scan")
                raise NotImplementedError()
