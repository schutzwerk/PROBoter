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

import os
import re
import time
import asyncio
import logging
from typing import Tuple

import cv2
import numpy as np


from proboter.hardware import StaticCamera, CameraStatus, CameraException, \
    CameraNotConnectedException
from proboter.event_bus import EventBus
from proboter.model import StaticCameraConfig


class UsbStaticCamera(StaticCamera):
    """
    A static camera system attached via USB
    """

    log = logging.getLogger(__module__)

    def __init__(self, camera_config: StaticCameraConfig,
                 camera_index: int,
                 event_bus: EventBus):
        """
        Initialize a new USB static camera

        :param camera_config: Camera configuration
        :type camera_config: StaticCameraConfig
        :param event_bus: Global event bus
        :type event_bus: EventBus
        """
        StaticCamera.__init__(self,
                              camera_config,
                              CameraStatus(id=camera_config.id,
                                           name=camera_config.name,
                                           index=camera_index,
                                           resolution=(camera_config.resolution_width,
                                                       camera_config.resolution_height),
                                           connected=False),
                              event_bus)

        self._usb_camera_id = None
        self._usb_monitor = None
        self._usb_camera_device = None

        self._capture_lock = asyncio.Lock()
        self._capture_device = cv2.VideoCapture()

        self._polling_task = None

    async def start(self) -> None:
        """
        Set up and initialize the USB camera
        """
        # Check if device exists
        if not os.path.exists(self.config.usb_device_name):
            self.log.warning("Configured camera device not found")
            self.status.connected = False
            self._usb_camera_device = None
        else:
            self.log.info("Using camera device %s",
                          self.config.usb_device_name)
            self.status.connected = True
            self._usb_camera_device = self.config.usb_device_name

        # Try to open the camera as capture device
        if self._usb_camera_device is not None:
            # Resolve the camera ID
            camera_path = self._usb_camera_device
            if os.path.islink(camera_path):
                camera_path = os.path.realpath(camera_path)
                self.log.info("Resolved camera symbolic link to %s",
                              camera_path)

            # Extract the camera ID
            # TODO Improve the ID extraction with a regex
            match = re.match(r".*/video(?P<cam_id>[0-9]+)$", camera_path)
            if not match:
                raise CameraException(
                    f"Invalid camera device name: {camera_path:s}")

            # Try to open the camera as capture device
            self._usb_camera_id = int(match.group('cam_id'))
            self.log.info("Opening camera %d", self._usb_camera_id)
            self._capture_device.open(self._usb_camera_id)

            if not self._capture_device.isOpened():
                self.log.error("Unable to open camera '%s'",
                               self._usb_camera_id)
                self._capture_device.release()
                self._usb_camera_id = None
                self.status.connected = False
            else:
                self.log.info("Successfully opened camera %d",
                              self._usb_camera_id)
                self.status.connected = True
                # Limit the OpenCV internal frame buffer to a single frame
                self._capture_device.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                # Set the current resolution
                self._capture_device.set(cv2.CAP_PROP_FRAME_WIDTH,
                                         self.config.resolution_width)
                self._capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT,
                                         self.config.resolution_height)
                # Start the video feed polling task
                self._polling_task = asyncio.create_task(
                    self._poll_video_feed())

        # Inform about the current camera status
        await self._status_changed()

    async def stop(self) -> None:
        """
        Shutdown the camera
        """
        if self.status.connected:
            # Cancel the video feed polling task
            self._polling_task.cancel()
            await self._polling_task
            self._polling_task = None
            # Release the camera
            self._capture_device.release()
            self._capture_device = None
            self._usb_camera_id = None

        self._status.connected = False
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
        if not self.status.connected:
            raise CameraNotConnectedException()

        async with self._capture_lock:
            # Try to set the camera resolution
            width = resolution[0]
            height = resolution[1]
            self._capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

            # Grab the next available camera frame
            frame = None
            while frame is None:
                _, frame = self._capture_device.read()

            # Restore the camera resolution
            width = self.resolution[0]
            height = self.resolution[1]
            self._capture_device.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._capture_device.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

        # Undistort the camera frame
        frame = self._undistort_frame(
            frame, resolution) if undistort else frame

        return frame

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

    async def _poll_video_feed(self) -> None:
        """
        Poll the camera for new frames
        """
        try:
            framerate_delay = 1.0 / self.config.framerate

            while True:
                t_start = time.time()
                async with self._capture_lock:
                    # Grab the next camera frame
                    frame = None
                    while frame is None:
                        _, frame = self._capture_device.read()
                        if frame is None:
                            await asyncio.sleep(0.01)

                # Inform about a new frame
                await self._new_camera_frame(frame)

                # Wait for the next frame
                elapsed = time.time() - t_start
                sleep_time = framerate_delay - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    framerate_delay *= 2.0
                    self.log.info("Reduced frame rate to %.1f due to possible overload",
                                  1.0 / framerate_delay)

        except asyncio.CancelledError:
            self.log.info("Stopping video feed poll task")
