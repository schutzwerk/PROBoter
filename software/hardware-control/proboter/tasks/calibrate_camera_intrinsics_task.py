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

"""
Source code inspired by the lecture 'Augmented Reality' of Prof. Ulhaas (HS Kempten) and ported
to Python.


Original copyright:
-------------------
This file contains material supporting chapter 9 of the cookbook:
Computer Vision Programming using the OpenCV Library.
by Robert Laganiere, Packt Publishing, 2011.
This program is free software; permission is hereby granted to use, copy, modify,
and distribute this source code, or portions thereof, for any purpose, without fee,
subject to the restriction that the copyright notice may not be removed
or altered from any source or altered source distribution.
The software is released on an as-is basis and without any warranties of any kind.
In particular, the software is not guaranteed to be fault-tolerant or free from failure.
The author disclaims all warranties with regard to this software, any use,
and any consequent failure, is purely the responsibility of the user.

Copyright (C) 2010-2011 Robert Laganiere, www.laganiere.name
"""

import logging
from typing import Tuple, List
from dataclasses import dataclass

import cv2
import numpy as np
from pydantic import Field

from proboter.fields import NumpyArray

from .task import Task
from .exceptions import ChessboardCameraCalibrationException


@dataclass
class CalibrateCameraIntrinsicsParameter:
    """
    Camera intrinsics calibration parameter
    """
    grid_size_x: float
    grid_size_y: float
    field_size_x: float
    field_size_y: float
    snapshots: List = Field(default_factory=list)
    debug: bool = False

    @property
    def grid_size(self) -> Tuple[float, float]:
        """
        Return the calibration pattern grid as tuple of [width, height]
        :rtype: Tuple[float, float]
        """
        return [self.grid_size_x, self.grid_size_y]

    @property
    def field_size(self) -> Tuple[float, float]:
        """
        Return the calibration pattern field size as tuple of [width, height]
        :rtype: Tuple[float, float]
        """
        return [self.field_size_x, self.field_size_y]


@dataclass
class CalibrateCameraIntrinsicsResult:
    """
    Camera intrinsics calibration result
    """
    camera_matrix: NumpyArray = Field(np_shape=(3, 3))
    distortion_coefficients: NumpyArray = Field(np_shape=(1, 5))


class CalibrateCameraIntrinsicsTask(
        Task[CalibrateCameraIntrinsicsParameter, CalibrateCameraIntrinsicsResult]):
    """
    Task to calibrate camera intrinsic parameters
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: CalibrateCameraIntrinsicsParameter):
        """
        Initialize a new camera intrinsic calibration task
        """
        super().__init__("CalibrateCameraIntrinsics", params)

        self.image_points = []
        self.object_points = []
        self.projection_matrix = None
        self.camera_matrix = None
        self.dist_coeffs = None
        self.map1 = None
        self.map2 = None
        self.must_init_undistort = True

    async def run(self) -> CalibrateCameraIntrinsicsResult:
        """
        Calibrate a static camera system by taking a snapshot of a
        reference board
        """
        # Add all taken chessboard images
        self.add_chessboard_points(self.params.snapshots,
                                   self.params.grid_size,
                                   self.params.field_size)

        # Calculate the camera intrinsic parameters
        self.calibrate(image_size=(self.params.snapshots[0].shape[0],
                                   self.params.snapshots[0].shape[1]))
        # Debug output
        if self.params.debug:
            for idx, img in enumerate(self.params.snapshots):
                undist_img = self.remap(img)
                cv2.imwrite(f'./undist_img_{idx}.png', undist_img)

        return CalibrateCameraIntrinsicsResult(camera_matrix=self.camera_matrix,
                                               distortion_coefficients=self.dist_coeffs)

    def add_chessboard_points(self, chessboard_images,
                              board_size, field_size=(28.0, 28.0)):
        """
        Extract corner points from chessboard images

        :param chessboard_images: A list of chessboard images (numpy arrays)
        :param board_size: A tuple of (height, width) describing the chessboard size
                           (count of chessboard fields along the width and height)
        :param field_size: The size of a chessboard field as a tuple of (width, height)
                           in mm
        """

        # 3D Scene Points:
        # Initialize the chessboard corners
        # in the chessboard reference frame
        # The corners are at 3D location (X,Y,Z)= (i,j,0)
        object_corners = np.empty((0, 3), np.float32)
        for i in range(board_size[1]):
            for j in range(board_size[0]):
                object_corner = np.array(
                    [i * field_size[0], j * field_size[1], 0.0]).reshape(1, 3)
                object_corners = np.append(
                    object_corners, object_corner, axis=0)
        object_corners = object_corners.astype(np.float32)

        # 2D Image points:
        successes = 0
        # for all viewpoints
        for i, image in enumerate(chessboard_images):
            self.log.info("Processing image %d of %d",
                          i + 1, len(chessboard_images))
            # Get the chessboard corners
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            found, image_corners = cv2.findChessboardCorners(image_gray, board_size, image_gray,
                                                             flags=cv2.CALIB_CB_ADAPTIVE_THRESH)

            if not found:
                self.log.warning(
                    "Ignoring image %d. No chessboard corners found.", i + 1)
                continue

            # Get subpixel accuracy on the corners
            try:
                image_corners = cv2.cornerSubPix(image=image_gray,
                                                 corners=image_corners,
                                                 winSize=(11, 11),
                                                 zeroZone=(-1, -1),
                                                 criteria=(cv2.TERM_CRITERIA_EPS
                                                           + cv2.TERM_CRITERIA_MAX_ITER,
                                                           30,
                                                           0.1))
            except cv2.error as exc:
                self.log.warning(
                    "Ignoring image %d due to error: %s", i + 1, exc)
                continue

            # If we have a good board, add it to our data
            if len(image_corners) == board_size[0] * board_size[1]:
                # Add image and scene points from one view
                self._add_points(image_corners, object_corners)
                successes += 1

            # Draw the corners
            if self.params.debug:
                tmp_image = image.copy()
                cv2.drawChessboardCorners(
                    tmp_image, board_size, image_corners, found)
                cv2.imwrite(f'./chessboard_results_{i}.png', tmp_image)

        return successes

    def calibrate(self, image_size):
        """"
        Calculate the intrinsic camera parameters based on the
        previously added chessboard points

        :param image_size: The size of the camera frame or subsection as tuple
                           of (width, height) in pixel
        """
        # Start calibration
        try:
            _, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
                self.object_points, self.image_points, image_size, None, None)
        except cv2.error as exc:
            raise ChessboardCameraCalibrationException(str(exc)) from None

        rotation_mat = np.zeros((3, 3))
        r_mat = cv2.Rodrigues(rvecs[0], rotation_mat)[0]
        p_mat = np.column_stack((np.matmul(camera_matrix, r_mat), tvecs[0]))

        self.camera_matrix = camera_matrix
        self.dist_coeffs = dist_coeffs
        self.projection_matrix = p_mat

        self.must_init_undistort = True

    def remap(self, image):
        """
        Remove distortion in an image (after calibration)

        :param image:
        :return:
        """
        # called once per calibration
        if self.must_init_undistort:
            # Build the maps for the 'remap' inverse mapping algorithm
            map1, map2 = cv2.initUndistortRectifyMap(
                self.camera_matrix,
                self.dist_coeffs,
                None,
                self.camera_matrix,
                (image.shape[1], image.shape[0]),
                m1type=cv2.CV_32FC1)

            self.map1 = map1
            self.map2 = map2
            self.must_init_undistort = False

        # Apply mapping functions
        undistorted = cv2.remap(image, self.map1, self.map2, cv2.INTER_LINEAR)
        return undistorted

    def _add_points(self, image_corners, object_corners):
        """
        Add scene points and corresponding image points

        :param image_corners:
        :param object_corners:
        :return:
        """
        # 2D image points from one view
        self.image_points.append(image_corners)
        # corresponding 3D scene points
        self.object_points.append(object_corners)
