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
from typing import Tuple

import numpy as np

from proboter.hardware import StaticCamera, CameraStatus
from proboter.event_bus import EventBus
from proboter.model import StaticCameraConfig


class SimulationStaticCamera(StaticCamera):
    """
    A simulated static camera system
    """

    log = logging.getLogger(__module__)

    def __init__(self, camera_config: StaticCameraConfig,
                 camera_index: int,
                 event_bus: EventBus):
        StaticCamera.__init__(self,
                              camera_config,
                              CameraStatus(id=camera_config.id,
                                           name=camera_config.name,
                                           index=camera_index,
                                           resolution=(camera_config.resolution_width,
                                                       camera_config.resolution_height),
                                           connected=False),
                              event_bus)

    async def start(self) -> None:
        """
        Open the camera / capture device and setup the USB
        monitor to detect hardware setup changes
        """
        self.log.info("Starting simulation camera '%s'", self.name)
        self.status.connected = True
        await self._status_changed()

    async def stop(self) -> None:
        """
        Close the camera
        """
        self.log.info("Stopping simulation camera '%s'", self.name)
        self.status.connected = False
        await self._status_changed()

    async def capture_snapshot(self, resolution: Tuple[int, int] = None,
                               undistort: bool = False) -> np.ndarray:
        """
        Capture a snapshot with a given camera resolution.

        The continuously camera feed is blocked while the
        snapshot capturing is in progress!

        :param resolution: The snapshot resolution as tuple of
                           (width, height) in pixel
        :param undistort: Whether the image should be undistorted
        :return: The undistorted snapshot. Important: It is not
                 guaranteed that the snapshot is made with the
                 given resolution so additional checks have to
                 be made!
        """
        # Return a dummy black image
        return np.zeros((resolution[1],
                         resolution[0],
                         3), dtype=np.uint8)

    def map_image_to_global_points(self, image_points: np.ndarray,
                                   z_distance: float) -> np.ndarray:
        """
        Transform image points to points in the global coordinate system

        :param image_points: The image points to transform as n x 2 numpy array
        :param z_distance: The z distance to the currently viewed plane
        :return: The corresponding points in the global system as n x 3 numpy array
        """
        raise NotImplementedError()

    def map_global_to_image_points(
            self, global_points: np.ndarray) -> np.ndarray:
        """
        Transform points from the global system to the image plane

        :param global_points: The points in the global coordinate system to
                              transform as n x 3 numpy array
        :return: The corresponding points in the image plane as
                 n x 2 numpy array
        """
        raise NotImplementedError()
