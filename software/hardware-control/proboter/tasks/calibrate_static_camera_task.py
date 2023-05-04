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
from proboter.model import ReferenceBoardConfig

from .task import Task
from .utils import ReferenceBoard


@dataclass
class CalibrateStaticCameraParameter:
    """
    Static camera calibration parameter
    """
    # ID of the reference board to use
    reference_board: int
    # Brightness threshold for image binarization
    brightness_threshold: int
    # Number of calibration runs to perform
    num_calibration_runs: int = 1
    # Image resolution
    image_resolution: NumpyArray = Field(np_shape=2)
    # Whether to run in debug mode
    debug: bool = False


@dataclass
class CalibrateStaticCameraResult:
    """
    Static camera calibration results
    """
    # Unique of the calibrated static camera system
    camera: int = -1
    # The (4x4) transformation matrix defining the static camera pose
    tmat: NumpyArray = Field(default_factory=lambda: np.eye(4),
                             np_shape=(4, 4))
    # Residuals from the mapping of the measured pin centers in the camera frame
    # to the reference coordinates of the reference board as (4x3) numpy array
    residuals_local_to_global: NumpyArray = Field(
        default_factory=lambda: np.zeros((4, 3)),
        np_shape=(4, 3))
    # Residuals from the mapping of the reference coordinates of the reference
    # board to the measured pin centers in the camera frame as (4x2) numpy
    # array
    residuals_global_to_local: NumpyArray = Field(
        default_factory=lambda: np.zeros((4, 2)),
        np_shape=(4, 2))
    # Max. absolute residuals from the mapping of the reference pin locations of the
    # reference board to the measured pin centers in the camera frame as 2D
    # vector
    max_residuals_global_to_local: NumpyArray = Field(
        default_factory=lambda: np.zeros((2,)),
        np_shape=2)
    # Max. absolute residuals from the mapping of the reference pin locations in
    # the camera image to the reference board as 3D vector
    max_residuals_image_to_global: NumpyArray = Field(
        default_factory=lambda: np.zeros((3,)),
        np_shape=3)


class CalibrateStaticCameraTask(
        Task[CalibrateStaticCameraParameter, CalibrateStaticCameraResult]):
    """
    Task to calibrate a single static camera system
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: CalibrateStaticCameraParameter,
                 camera: StaticCamera,
                 reference_board_config: ReferenceBoardConfig):
        """
        Initialize a new static camera calibration task
        """
        super().__init__("CalibrateStaticCamera", params)
        self._camera = camera
        self._reference_board = ReferenceBoard(reference_board_config)

    async def run(self) -> CalibrateStaticCameraResult:
        """
        Calibrate a static camera system by taking a snapshot of a
        reference board
        """
        # Get the current camera frame
        image = await self._camera.capture_snapshot(resolution=self.params.image_resolution,
                                                    undistort=True)

        # Important: Because the snapshot is already undistorted we set
        #            the distortion coefficients to all zeros!
        dist_coefficients = np.zeros(5)

        # 1. Search for reference pins defined by the QR code-like markers
        marker_ref_matches = self._reference_board.\
            search_marker_reference_points(image,
                                           camera_matrix=self._camera.config.camera_matrix,
                                           dist_coefficients=dist_coefficients,
                                           contour_epsilon=10.0,
                                           use_corner_refinement=True,
                                           debug=self.params.debug)

        # Estimate the camera pose based on the identified
        tmat = self._reference_board.estimate_camera_pose(marker_ref_matches,
                                                          self._camera.config.camera_matrix,
                                                          dist_coefficients)

        # 2. Search for additional reference pins in the image
        threshold = self.params.brightness_threshold
        ref_pin_matches = self._reference_board \
            .search_plane_pin_reference_points(image,
                                               tmat,
                                               self._camera.config.camera_matrix,
                                               brightness_threshold=threshold,
                                               debug=self.params.debug)

        # 3. Combine all identified reference points
        ref_matches = []
        ref_matches += ref_pin_matches

        # 4. Finally calculate the camera pose taking all
        # reference points into account
        tmat = self._reference_board.estimate_camera_pose(ref_matches,
                                                          self._camera.config.camera_matrix,
                                                          dist_coefficients)

        if self.params.debug:
            self._reference_board.visualize_estimated_pose_results(
                image, ref_matches, tmat, self._camera.config.camera_matrix)

        self.log.debug("Calculated camera pose: %s", tmat)

        # Calculate the calibration errors in the local (image) system
        ref_points_global = np.array([match.reference_point
                                      for match in ref_matches])
        ref_points_image = np.array([match.image_point
                                     for match in ref_matches])
        calc_image_points = self._reference_board.\
            global_to_image_points(ref_points_global, tmat,
                                   self._camera.config.camera_matrix)

        residuals_global_to_local = ref_points_image - calc_image_points
        self.log.debug("Residuals global -> image: %s",
                       residuals_global_to_local)

        # Calculate the calibration errors in the global (reference) system
        calc_global_ref_pins = self._reference_board.\
            calculate_image_to_global_points(tmat,
                                             self._camera.config.camera_matrix,
                                             ref_points_image.astype(np.float_))
        residuals_image_to_global = ref_points_global - calc_global_ref_pins
        self.log.debug("Residuals image -> global: %s",
                       residuals_image_to_global)

        return CalibrateStaticCameraResult(camera=self._camera.id,
                                           tmat=tmat.T,
                                           residuals_global_to_local=residuals_global_to_local,
                                           residuals_local_to_global=residuals_image_to_global,
                                           max_residuals_global_to_local=np.max(
                                               np.abs(residuals_global_to_local), 0),
                                           max_residuals_image_to_global=np.max(
                                               np.abs(residuals_image_to_global), 0))
