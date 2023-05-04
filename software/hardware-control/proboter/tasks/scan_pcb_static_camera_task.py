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
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from proboter.fields import NumpyArray
from proboter.hardware import StaticCamera
from proboter.storage import PcbScan, PcbScanImage

from .task import Task


@dataclass
class ScanPcbStaticCameraParameter:
    """
    Parameters to define a PCB scan
    """
    # ID of the PCB the scan belongs to
    pcb_id: int = Field()
    # Name of the new scan
    name: str = Field()
    # Scan area in X direction [min, max] (in the global system)
    x_range: NumpyArray = Field(np_shape=2)
    # Scan area in Y direction [min, max] (in the global system)
    y_range: NumpyArray = Field(np_shape=2)
    # Z offset of the PCB / scan plane in mm
    z_offset: float = 0.0
    # Used camera resolution for the scan
    image_resolution: NumpyArray = Field(np_shape=2)


@dataclass
class ScanPcbStaticCameraResult:
    """
    PCB scan result
    """
    # ID of the newly created PCB scan
    scan: int


class ScanPcbStaticCameraTask(
        Task[ScanPcbStaticCameraParameter, ScanPcbStaticCameraResult]):
    """
    Task that scans a rectangular PCB area utilizing a static camera system.
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: ScanPcbStaticCameraParameter,
                 camera: StaticCamera):
        """
        Initialize a new PCB scan task
        """
        super().__init__("ScanPcbStaticCamera", params)
        self._camera = camera

    async def run(self) -> ScanPcbStaticCameraResult:
        """
        Scan a board / area with the static camera

        :return: The PCB scan result
        :rtype: ScanPcbStaticCameraResult
        """
        self.log.debug("Start PCB scan with static camera: %s", self.params)

        # Prepare the resulting scan
        scan = PcbScan(pcb_id=self.params.pcb_id,
                       name=self.params.name,
                       x_min=self.params.x_range[0],
                       x_max=self.params.x_range[1],
                       y_min=self.params.y_range[0],
                       y_max=self.params.y_range[1],
                       z_offset=self.params.z_offset)

        # Take a snapshot with the static camera
        self.log.debug("Taking picture of PCB")
        pcb_image = await self._camera.capture_snapshot(self.params.image_resolution,
                                                        undistort=True)

        scan_image = PcbScanImage(scan=scan,
                                  tmat=np.linalg.inv(
                                      self._camera.config.tmat_to_global),
                                  camera_matrix=np.linalg.inv(
                                      self._camera.config.camera_matrix),
                                  image=pcb_image,
                                  z_offset=self.params.z_offset)

        # Save both, the PCB scan and the scan image
        await scan.save()
        await scan_image.save()

        return ScanPcbStaticCameraResult(scan.id)
