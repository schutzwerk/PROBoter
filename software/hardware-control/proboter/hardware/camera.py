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

import asyncio
from abc import abstractmethod
from typing import List, Tuple, AsyncGenerator

import cv2
import numpy as np

from proboter.event_bus import EventBus
from proboter.model import CameraConfig

from .hardware_unit import HardwareUnit
from .events import CameraStatus, CameraStatusChangedEvent


class Camera(HardwareUnit[CameraConfig, CameraStatus]):
    """
    Interface of a calibrated camera which can continuously stream
    the camera feed or capture single snapshots
    """

    def __init__(self, config: CameraConfig, status: CameraStatus,
                 event_bus: EventBus) -> None:
        HardwareUnit.__init__(self, config, status)
        self._event_bus = event_bus
        self._stream_queues: List[asyncio.Queue] = []

    @property
    def id(self) -> int:
        """
        Return the camera id
        """
        return self.config.id

    @property
    def name(self) -> str:
        """
        Return the camera name
        """
        return self.config.name

    @property
    def resolution(self) -> Tuple[int, int]:
        """
        Return the camera resolution as tuple of (width, height)
        """
        return (self.config.resolution_width,
                self.config.resolution_height)

    async def stream(self) -> AsyncGenerator[np.ndarray, None]:
        """
        Return the camera live feed as an async. generator of
        PNG encoded images

        :return: Camera feed generator
        :rtype: AsyncGenerator[np.ndarray, None]
        """
        frame_queue = asyncio.Queue()
        self._stream_queues.append(frame_queue)
        try:
            while True:
                frame = await frame_queue.get()
                yield frame
        finally:
            self._stream_queues.remove(frame_queue)

    @abstractmethod
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

    @abstractmethod
    def map_image_to_global_points(self, image_points: np.ndarray,
                                   z_distance: float) -> np.ndarray:
        """
        Transform image points to points in the global coordinate system

        :param image_points: The image points to transform as n x 2 numpy array
        :param z_distance: The z distance to the currently viewed plane
        :return: The corresponding points in the global system as n x 3 numpy array
        """

    @abstractmethod
    def map_global_to_image_points(
            self, global_points: np.ndarray) -> np.ndarray:
        """
        Transform points from the global system to the image plane

        :param global_points: The points in the global coordinate system to
                              transform as n x 3 numpy array
        :return: The corresponding points in the image plane as
                 n x 2 numpy array
        """

    def approximate_distance_from_two_plane_points(self, point1: np.ndarray,
                                                   point2: np.ndarray,
                                                   real_distance: float) -> float:
        """
        Calculate the distance of the camera to a plane from two given
        image points and the real distance between these points

        The result is only accurate if the two real points are at
        a plane that is absolutely parallel to the image plane!
        :param point1: The first image point as (1x2) vector in pixel
        :param point2: The second image point as (1x2) vector in pixel
        :param real_distance: The real distance between the two points
        :return: The calculated distance of the plane point and the camera
                 origin in z direction
        """
        p_diff = point2 - point1
        mat = np.matmul(np.linalg.inv(self.config.camera_matrix[0:2, 0:2]),
                        p_diff)
        mat = np.sqrt(np.sum(np.square(mat)))
        dist = real_distance / mat

        return dist

    def map_image_plane_to_camera_points(self, image_points: np.ndarray,
                                         z_distance: float) -> np.ndarray:
        """
        Convert image plane points to points in the camera system

        :param image_points: The image plane points to transform as (nx2) numpy array
        :type image_points: np.ndarray
        :param z_distance: The distance of the projection plane
        :type z_distance: np.ndarray
        :return: The corresponding points in the camera system as (nx3) numpy array
        :rtype: np.ndarray
        """
        # Extend the points to 2D homogeneous coordinates
        points = np.ones((image_points.shape[0], 3))
        points[:, 0:2] = image_points
        points *= z_distance

        return np.matmul(np.linalg.inv(self.config.camera_matrix),
                         points.T).T

    def _undistort_frame(self, frame: np.ndarray,
                         resolution=None) -> np.ndarray:
        """
        Undistort a given camera frame

        :param frame: Image to undistort
        :type frame: np.ndarray
        :return: Undistorted image
        :rtype: np.ndarray
        """
        # Initialize the undistortion maps
        map1, map2 = cv2.initUndistortRectifyMap(
            self.config.camera_matrix,
            self.config.distortion_coefficients,
            None,
            self.config.camera_matrix,
            self.resolution if resolution is None else resolution,
            m1type=cv2.CV_32FC1)

        # Undistort the camera frame
        return cv2.remap(frame, map1, map2, cv2.INTER_LINEAR)

    async def _status_changed(self) -> None:
        """
        Inform about the camera status change by sending
        a 'CameraStatusChangedEvent' on the event bus
        """
        # Create an event on the event bus
        event = CameraStatusChangedEvent(id=self.config.id,
                                         status=self.status)
        await self._event_bus.emit_event(event)

    async def _new_camera_frame(self, frame: np.ndarray) -> None:
        """
        Inform about a new camera frame

        The frame is converted to a PNG image and then passed to
        all registered camera feed readers

        :param frame: New camera frame
        :type frame: np.ndarray
        """

        encoding_param = [int(cv2.IMWRITE_JPEG_QUALITY), 70]
        _, frame_png = cv2.imencode(".jpeg", frame, encoding_param)
        frame_bytes = frame_png.tobytes()
        for stream_queue in self._stream_queues:
            await stream_queue.put(frame_bytes)
