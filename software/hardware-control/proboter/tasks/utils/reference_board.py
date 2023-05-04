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
from random import randint
from dataclasses import dataclass
from typing import Iterable, Tuple

import cv2
import numpy as np
from scipy import optimize

from mtracker import MarkerTracker, HammingMarkerIdentifier

from proboter.model import ReferenceBoardConfig


class ReferenceBoardException(Exception):
    """
    Base class for all exceptions related to the reference board
    """


@dataclass
class ReferencePointMatch:
    """
    A reference point match identified in an image
    of the reference board
    """
    # 2D image point
    image_point: np.ndarray
    # Corresponding 3D reference point
    reference_point: np.ndarray


class ReferenceBoard:
    """
    A reference pattern definition:

                               D7_outer

            D7_ext(z=-12)                    D7_ext(z=-6)

                                 >>width<<

                                     ^ (Y)
                                     |
                        D7-----------|--------D10
                        |            |         |   ^
        D7_outer    <---------------(0,0)      | height      D7_outer
                   (X)  |                      |   v
                        D9---------------------D8


            D7_ext(z=-8)                   D7_ext(z=-10)

                                D7_outer
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: ReferenceBoardConfig):
        """
        Initialize a pattern with it's geometric dimensions

        :param config: Configuration of the reference board
        :type config: ReferenceBoardConfig
        """
        self._config = config

        # Z level of the reference board artificial coordinate system
        z0_plane = -config.thickness * 0.5
        self.marker_size = (config.marker_width, config.marker_height)

        self.inner_brass_pin_size = (config.inner_brass_pin_width,
                                     config.inner_brass_pin_height)
        self.raised_brass_pin_size = (config.raised_brass_pin_width,
                                      config.raised_brass_pin_height)
        self.marker_id_position_map = {
            1: np.array((config.marker_grid_width * 0.5,
                         config.marker_grid_height * 0.5,
                         z0_plane)),
            3: np.array((-config.marker_grid_width * 0.5,
                         config.marker_grid_height * 0.5,
                         z0_plane)),
            6: np.array((config.marker_grid_width * 0.5,
                         -config.marker_grid_height * 0.5,
                         z0_plane)),
            12: np.array((-config.marker_grid_width * 0.5,
                          -config.marker_grid_height * 0.5,
                          z0_plane))
        }
        self.outer_white_pin_positions = (
            np.array((config.outer_white_pin_width * 0.5,
                      config.outer_white_pin_height * 0.5,
                      z0_plane)),
            np.array((-config.outer_white_pin_width * 0.5,
                      config.outer_white_pin_height * 0.5,
                      z0_plane)),
            np.array((config.outer_white_pin_width * 0.5,
                      -config.outer_white_pin_height * 0.5,
                      z0_plane)),
            np.array((-config.outer_white_pin_width * 0.5,
                      -config.outer_white_pin_height * 0.5,
                      z0_plane)),
        )
        self.outer_brass_pin_positions = (
            np.array((config.outer_brass_pin_width * 0.5,
                      0,
                      z0_plane)),
            np.array((0,
                      config.outer_brass_pin_height * 0.5,
                      z0_plane)),
            np.array((-config.outer_brass_pin_width * 0.5,
                      0,
                      z0_plane)),
            np.array((0,
                      -config.outer_brass_pin_height * 0.5,
                      z0_plane)),
        )
        self.inner_brass_pin_position_map = {
            7: np.array((self.inner_brass_pin_size[0] * 0.5,
                         self.inner_brass_pin_size[1] * 0.5,
                         z0_plane)),
            8: np.array((-self.inner_brass_pin_size[0] * 0.5,
                         -self.inner_brass_pin_size[1] * 0.5,
                         z0_plane)),
            9: np.array((self.inner_brass_pin_size[0] * 0.5,
                         -self.inner_brass_pin_size[1] * 0.5,
                         z0_plane)),
            10: np.array((-self.inner_brass_pin_size[0] * 0.5,
                          self.inner_brass_pin_size[1] * 0.5,
                          z0_plane)),
        }
        self.raised_brass_pin_positions = (
            np.array((0.5 * self.raised_brass_pin_size[0],
                      0.5 * self.raised_brass_pin_size[1],
                      -12 + z0_plane)),
            np.array((-0.5 * self.raised_brass_pin_size[0],
                      -0.5 * self.raised_brass_pin_size[1],
                      -10 + z0_plane)),
            np.array((0.5 * self.raised_brass_pin_size[0],
                      -0.5 * self.raised_brass_pin_size[1],
                      -8 + z0_plane)),
            np.array((-0.5 * self.raised_brass_pin_size[0],
                      0.5 * self.raised_brass_pin_size[1],
                      -6 + z0_plane))
        )

    @property
    def id(self) -> int:
        """
        Return the unique identifier of the reference board
        """
        return self._config.id

    @property
    def name(self) -> str:
        """
        Return the displayable name of the reference board
        """
        return self._config.name

    @property
    def width(self) -> float:
        """
        Return the reference board width
        """
        return self._config.inner_brass_pin_width

    @property
    def height(self) -> float:
        """
        Return the reference board height
        """
        return self._config.inner_brass_pin_height

    @property
    def ext_width(self) -> float:
        """
        Return the distance of the outer four reference pins in X dimension
        """
        return self._config.raised_brass_pin_width

    @property
    def ext_height(self) -> float:
        """
        Return the distance of the outer four reference pins in Y dimension
        """
        return self._config.raised_brass_pin_height

    @property
    def reference_pin_coordinates(self) -> np.ndarray:
        """
        Return the reference pin absolute coordinates sorted by
        the reference pin diameters starting with the largest
        D10, D9, D8, D7
        """
        abs_pin_coords = np.zeros((4, 3), dtype=np.float32)
        abs_pin_coords[0, :] = self.get_reference_pin_coordinates_by_diameter(10)[
            1]
        abs_pin_coords[1, :] = self.get_reference_pin_coordinates_by_diameter(9)[
            1]
        abs_pin_coords[2, :] = self.get_reference_pin_coordinates_by_diameter(8)[
            1]
        abs_pin_coords[3, :] = self.get_reference_pin_coordinates_by_diameter(7)[
            1]

        return abs_pin_coords

    @property
    def reference_pin_indices_sorted(self) -> Iterable[int]:
        """
        Return the indices used for the inner reference pins
        sorted by their radius starting with the largest
        D10, D9, D8, D7
        """
        return [0, 1, 2, 3]

    @property
    def ext_reference_pin_coordinates(self) -> np.ndarray:
        """
        The coordinates of the extended reference pattern (4 reference pins
        in different heights) starting with the reference pin in the right upper
        corner (z=12) and the other pins in counter-clock wise direction
        (z=8, z=10, z=6)
        """
        return np.array(self.raised_brass_pin_positions, dtype=np.float32)

    def get_reference_pin_coordinates_by_diameter(self, diameter: float,
                                                  epsilon: float = 0.3) -> Tuple[int, np.ndarray]:
        """
        Get the coordinates of an inner reference pin by it's diameter

        :param diameter: The reference pin diameter
        :param epsilon: The delta used to match the reference pins
        :return: A tuple of (idx, diameter) of the reference pin index in the
                 list of reference pins [10, 9, 8, 7] and the reference pin coordinates
                 as 3D numpy vector
        :raises ReferenceBoardException: If the diameter can not be matched to
                                         one of the reference pattern
        """
        if 7 - epsilon <= diameter <= 7 + epsilon:
            return 3, self.inner_brass_pin_position_map[7]
        if 8 - epsilon <= diameter <= 8 + epsilon:
            return 2, self.inner_brass_pin_position_map[8]
        if 9 - epsilon <= diameter <= 9 + epsilon:
            return 1, self.inner_brass_pin_position_map[9]
        if 10 - epsilon <= diameter <= 10 + epsilon:
            return 0, self.inner_brass_pin_position_map[10]

        raise ReferenceBoardException(
            f"Unknown reference pin diameter {diameter:.1f}")

    def search_marker_reference_points(self, frame: np.ndarray,
                                       camera_matrix: np.ndarray = np.eye(3),
                                       dist_coefficients: np.ndarray = np.zeros(
                                           5),
                                       contour_epsilon: float = 5.0,
                                       use_corner_refinement: bool = False,
                                       debug: bool = False) -> Iterable[ReferencePointMatch]:
        """
        Search for reference points defined by QR code-like markers on the
        reference board in a given image

        :param frame: (Partial) image of a reference board
        :type frame: np.ndarray
        :param camera_matrix: Calibration of the camera that generated the image
        :type camera_matrix: np.ndarray
        :param dist_coefficients: Distortion coefficients of the camera that
                                  generated the image
        :type dist_coefficients: np.ndarray
        :param use_corner_refinement: Whether the marker corners should be
                                      refined with subpixel accuracy. Otherwise,
                                      the marker corners are approximated with
                                      a rotated rectangle
        :type use_corner_refinement: bool
        :param debug: Whether additional debug output should be generated,
                      defaults to False
        :type debug: bool, optional
        :return: An iterable collection of detected reference point matches
        :rtype: Iterable[ReferencePointMatch]
        """
        # Search for known markers in the image
        self.log.debug("Searching for reference markers in image")
        marker_tracker = MarkerTracker(marker_size=self.marker_size,
                                       marker_identifier=HammingMarkerIdentifier(
                                           # [1, 3, 6, 12],
                                           marker_ids=tuple(range(255)),
                                           color_inverse=True,
                                           color_threshold=200,
                                           debug=debug),
                                       camera_matrix=camera_matrix,
                                       dist_coefficients=dist_coefficients,
                                       contour_epsilon=contour_epsilon,
                                       debug=debug)
        markers = marker_tracker.detect_markers(
            frame, use_corner_refinement)
        self.log.debug("%d reference markers found", len(markers))

        # Single and two-character variable names are accepted to improve readability of
        # mathematical formulas here!
        # pylint: disable=invalid-name
        def error_func(estimate, p3):
            # Reconstruct the rectangle description
            rect = ((estimate[0], estimate[1]),
                    (estimate[2], estimate[3]),
                    estimate[4])
            box = cv2.boxPoints(rect)

            distances = np.zeros((p3.shape[0], 4))
            for i in range(4):
                p1 = box[i]
                p2 = box[(i + 1) % 4]
                d = np.cross(p2 - p1, p3 - p1) / np.linalg.norm(p2 - p1)
                distances[:, i] = d.reshape(-1)

            min_distances = np.min(distances, axis=1)

            return min_distances

        optimize_marker_contour = True
        if optimize_marker_contour:
            # Refine the marker corners
            for i, marker in enumerate(markers):
                # Draw the contour in a blank mask
                mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                cv2.drawContours(mask, [marker.contour], -1, (255), 1)

                rect_orig = cv2.minAreaRect(marker.contour)

                init_estimate = np.array((rect_orig[0][0],
                                          rect_orig[0][1],
                                          rect_orig[1][0],
                                          rect_orig[1][1],
                                          rect_orig[2]), dtype=np.float32)

                res, _ = optimize.leastsq(
                    error_func, init_estimate, marker.contour, epsfcn=0.5)

                rect = ((res[0], res[1]),
                        (res[2], res[3]),
                        res[4])

                img = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

                # Draw the optimized rectangle
                draw_original = True
                draw_optimized = False
                if draw_optimized:
                    box = cv2.boxPoints(rect)
                    box = np.int0(box)
                    img = cv2.polylines(img, [box.astype(np.int32)],
                                        True, (0, 255, 0),
                                        1)

                if draw_original:
                    box = cv2.boxPoints(rect_orig)
                    box = np.int0(box)
                    img = cv2.polylines(img, [box.astype(np.int32)],
                                        True, (0, 0, 255),
                                        1)

                if debug:
                    cv2.imshow(f"Marker {i}", img)
                    cv2.waitKey()

                marker.image_points = box = cv2.boxPoints(rect)

        # Map the detected marker positions to locations on the reference board
        ref_point_matches = []
        for marker in markers:
            image_points = marker.image_points
            marker_ref_position = self.marker_id_position_map[marker.id]
            marker_local_points_rotated = marker.local_points.copy()
            marker_local_points_rotated[:, 0] *= -1
            reference_points = marker_local_points_rotated + \
                np.tile(marker_ref_position, (4, 1))
            for i in range(4):
                point_match = ReferencePointMatch(image_point=image_points[i, :],
                                                  reference_point=reference_points[i, :])
                ref_point_matches.append(point_match)

        self.log.debug("%d point correspondences generated from ref. marker search",
                       len(ref_point_matches))

        if debug:
            # Visualize the detected markers
            tmp_image = frame.copy()
            cv2.imwrite("./ref_markers.png", tmp_image)
            marker_tracker.draw_markers(tmp_image, markers)
            cv2.imshow("Detected markers", tmp_image)
            cv2.waitKey()

        return ref_point_matches

    def search_plane_pin_reference_points(self, frame: np.ndarray,
                                          estimated_tmat: np.ndarray,
                                          camera_matrix: np.ndarray = np.eye(
                                              3),
                                          brightness_threshold: int = 150,
                                          debug: bool = False) -> Iterable[ReferencePointMatch]:
        """[summary]

        :param frame: [description]
        :type frame: np.ndarray
        :param estimated_tmat: [description]
        :type estimated_tmat: np.ndarray
        :raises Exception: [description]
        :return: [description]
        :rtype: Iterable[ReferencePointMatch]
        """
        # Determine the thresholding algithms based on the mean
        # brightness value (V channel in the HSV colour space) of the image
        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        v_mean = cv2.mean(frame_hsv)[2]
        method = cv2.THRESH_OTSU if v_mean < brightness_threshold else cv2.THRESH_TRIANGLE

        # Thresholding of the gray scale image
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + method)
        if debug:
            cv2.imshow("Gray", gray)
            cv2.imshow("Thresholded", thresh)
            cv2.waitKey()

        # Find contours in the binary mask
        contours, _ = cv2.findContours(image=thresh,
                                       mode=cv2.RETR_EXTERNAL,
                                       method=cv2.CHAIN_APPROX_NONE)

        # Project all reference pin centers with Z=0 into the image
        ref_points = []
        ref_points += self.outer_white_pin_positions
        ref_points += self.outer_brass_pin_positions
        ref_points += self.inner_brass_pin_position_map.values()
        ref_points = np.array(ref_points)

        ref_points_ext = np.ones((ref_points.shape[0], 4))
        ref_points_ext[:, :3] = ref_points

        tmat_global_to_image = self.calculate_tmat_global_to_image(
            estimated_tmat, camera_matrix)

        image_points = np.matmul(tmat_global_to_image, ref_points_ext.T).T
        image_points /= np.repeat(image_points[:, 2], 3).reshape(-1, 3)

        # Visualize the projected ref. points together with the
        # identified contours
        if debug:
            tmp_image = frame.copy()
            for i in range(image_points.shape[0]):
                cv2.circle(img=tmp_image,
                           center=(int(image_points[i, 0]),
                                   int(image_points[i, 1])),
                           radius=3,
                           color=(0, 0, 255))
            for contour in contours:
                cv2.drawContours(image=tmp_image,
                                 contours=[contour],
                                 contourIdx=-1,
                                 color=(randint(0, 255), randint(
                                     0, 255), randint(0, 255)),
                                 thickness=2)
            cv2.imshow("Projected ref. points", tmp_image)
            cv2.waitKey()

        # Find the contours that belong to the projected ref. points
        ref_point_matches = []
        for i in range(image_points.shape[0]):
            for j, contour in enumerate(contours):
                is_inside = cv2.pointPolygonTest(contour,
                                                 (int(image_points[i, 0]),
                                                  int(image_points[i, 1])),
                                                 False)
                if is_inside >= 0:
                    self.log.debug(
                        "Contour for ref. pin %d found: %d", i, j)
                    # Calculate the contour
                    moments = cv2.moments(contour)
                    center_of_mass = np.array((int(moments['m10'] / moments['m00']),
                                               int(moments['m01'] / moments['m00'])))
                    ref_point_matches.append(
                        ReferencePointMatch(image_point=center_of_mass,
                                            reference_point=ref_points[i, :]))

        if debug:
            tmp_image = frame.copy()
            for i, match in enumerate(ref_point_matches):
                cv2.circle(img=tmp_image,
                           center=(int(match.image_point[0]),
                                   int(match.image_point[1])),
                           radius=3,
                           color=(0, 0, 255))
                cv2.circle(img=tmp_image,
                           center=(int(image_points[i, 0]),
                                   int(image_points[i, 1])),
                           radius=3,
                           color=(0, 255, 0))
            cv2.imshow("Matched contour points", tmp_image)
            cv2.waitKey()

        return ref_point_matches

    @ classmethod
    def estimate_camera_pose(cls, ref_point_matches: Iterable[ReferencePointMatch],
                             camera_matrix: np.ndarray = np.eye(3),
                             dist_coefficients: np.ndarray = np.zeros(5)) -> np.ndarray:
        """
        Estimate the camera pose based on image / reference point correspondences

        :param ref_point_matches: [description]
        :type ref_point_matches: Iterable[ReferencePointMatch]
        :param camera_matrix: [description]
        :type camera_matrix: np.ndarray
        :param dist_coefficients: [description]
        :type dist_coefficients: np.ndarray
        :raises Exception: [description]
        :return: [description]
        :rtype: np.ndarray
        """
        # Caclulate the camera pose based on all point correspondences
        cls.log.debug("Estimating camera pose from %d point correspondences",
                      len(ref_point_matches))
        ref_points = np.zeros((len(ref_point_matches), 1, 3), dtype=np.float32)
        image_points = np.zeros(
            (len(ref_point_matches), 1, 2), dtype=np.float32)
        for i, match in enumerate(ref_point_matches):
            ref_points[i, 0, :] = match.reference_point
            image_points[i, 0, :] = match.image_point

        success, r_vec, t_vec, indices = cv2.solvePnPRansac(objectPoints=ref_points,
                                                            imagePoints=image_points,
                                                            cameraMatrix=camera_matrix,
                                                            distCoeffs=dist_coefficients,
                                                            flags=cv2.SOLVEPNP_ITERATIVE)

        if not success:
            raise ReferenceBoardException("Camera pose estimation failed")

        cls.log.debug("%d of %d point correspondences used",
                      indices.shape[0], len(ref_point_matches))

        # Calculate the rotation matrix from
        # the Rodrigues angles
        r_mat, _ = cv2.Rodrigues(src=r_vec)

        # Store the complete marker transformation
        tmat = np.eye(4)
        tmat[0:3, 0:3] = r_mat
        tmat[0:3, 3] = t_vec.reshape(-1)

        computed_image_points = cls.global_to_image_points(ref_points.reshape(
            ref_points.shape[0], 3), tmat, camera_matrix)
        cls.log.debug("Input image points: %s", image_points.reshape(-1, 2))
        cls.log.debug("Computed image points: %s", computed_image_points)
        residuals_image = computed_image_points - \
            image_points.reshape(image_points.shape[0], 2)
        cls.log.debug("Residuals [px]: %s", residuals_image)

        return tmat

    @classmethod
    def calculate_tmat_global_to_image(cls, camera_pose: np.ndarray,
                                       camera_matrix: np.ndarray) -> np.ndarray:
        """
        Calculate the (3x4) transformation matrix from the global
        coordinate system to the image coordinate system

        :param camera_pose: The (4x4) transformation matrix defining the pose
                            of the camera system
        :type camera_pose: np.ndarray
        :param camera_matrix: The (3x3) camera calibration matrix containing
                              the camera intrinsic parameters
        :type camera_matrix: np.ndarray
        :return: The (3x4) transformation matrix that can be used to transform
                 arbitrary points from the global coordinate system to image
                 coordinates. After transformation, the resulting coordinates
                 must be normalized!
        :rtype: nd.ndarray
        """
        t_1 = camera_pose
        t_2 = np.eye(4)
        t_2 = t_2[:3, :]
        t_3 = camera_matrix
        tmat_global_to_image = np.matmul(t_2, t_1)
        tmat_global_to_image = np.matmul(t_3, tmat_global_to_image)

        return tmat_global_to_image

    @classmethod
    def global_to_image_points(cls, global_points: np.ndarray,
                               camera_pose: np.ndarray,
                               camera_matrix: np.ndarray) -> np.ndarray:
        """[summary]

        :param global_points: [description]
        :type global_points: np.ndarray
        :param camera_pose: [description]
        :type camera_pose: np.ndarray
        :param camera_matrix: [description]
        :type camera_matrix: np.ndarray
        :return: [description]
        :rtype: np.ndarray
        """

        global_points_ext = np.ones((global_points.shape[0], 4))
        global_points_ext[:, :3] = global_points

        tmat_global_to_image = cls.calculate_tmat_global_to_image(
            camera_pose, camera_matrix)

        image_points = np.matmul(tmat_global_to_image, global_points_ext.T).T
        image_points /= np.repeat(image_points[:, 2], 3).reshape(-1, 3)

        return image_points[:, 0:2]

    @classmethod
    def calculate_image_to_global_points(cls, camera_pose: np.ndarray,
                                         camera_matrix: np.ndarray,
                                         image_points: np.ndarray,
                                         z: float = 0) -> np.ndarray:
        """
        Calculate for a given set of image points the corresponding points
        on a plane parallel to the ref. system's XY plane

        :param camera_pose: Camera pose as (4x4) matrix
        :type camera_pose: np.ndarray
        :param camera_matrix: Camera matrix defining the camera's intrinsic
                              parameters as (3x3) matrix
        :type camera_matrix: np.ndarray
        :param image_points: Image points to transform as (nx2) array
        :type image_points: np.ndarray
        :param z: Optional offset in Z direction of the intersection plane,
                  defaults to 0.
        :type z: float
        :return: The transformed points as (nx3) matrix
        :rtype: np.ndarray
        """
        # Calculate the transformation matrix from the camera to the global
        # system
        t34 = np.eye(4)[:3, :]  # 3x4 pin hole camera projection
        pmat = np.matmul(t34, camera_pose)
        pmat = np.matmul(camera_matrix, pmat)

        # For each image point, the depth / z value is computed as the
        # intersection with the global system XY plane
        global_points = np.zeros((image_points.shape[0], 3))

        # Accept single character variables to improve readability of mathematical formulas here!
        # pylint: disable=invalid-name
        for i in range(image_points.shape[0]):
            u = image_points[i, 0]
            v = image_points[i, 1]

            # Solve a linear equation system to calculate the
            # ray / plane intersection
            a = np.zeros((3, 3))
            a[0, 0] = u
            a[1, 0] = v
            a[2, 0] = 1
            a[:, 1:] = -pmat[:, 0:2]

            b = z * pmat[:, 2] + pmat[:, 3]

            res = np.linalg.solve(a, b)
            # f = res[0]
            x = res[1]
            y = res[2]

            global_points[i, :] = np.array((x, y, z))

        return global_points

    @classmethod
    def visualize_estimated_pose_results(cls, frame: np.ndarray,
                                         ref_point_matches: Iterable[ReferencePointMatch],
                                         estimated_tmat: np.ndarray,
                                         camera_matrix: np.ndarray) -> None:
        """
        Visualize the results of a camera pose estimation

        :param frame: Camera frame into which the results will be drawn
        :type frame: np.ndarray
        :param ref_point_matches: Ref. point matches
        :type ref_point_matches: Iterable[ReferencePointMatch]
        :param estimated_tmat: Estimated camera transformation matrix
        :type estimated_tmat: np.ndarray
        :param camera_matrix: Camera calibration matrix
        :type camera_matrix: np.ndarray
        """
        tmp_image = frame.copy()
        for match in ref_point_matches:
            # Draw the detected image point
            cv2.circle(img=tmp_image,
                       center=(int(match.image_point[0]),
                               int(match.image_point[1])),
                       radius=5,
                       color=(0, 0, 255))

            # Calculate the projected point
            projected_point = cls.global_to_image_points(
                match.reference_point.reshape(-1, 1, 3),
                estimated_tmat,
                camera_matrix)
            projected_point = projected_point.reshape(2,)
            print("Projected point:", projected_point, (int(projected_point[0]),
                                                        int(projected_point[1])))
            cv2.circle(img=tmp_image,
                       center=(int(projected_point[0]),
                               int(projected_point[1])),
                       radius=10,
                       color=(255, 255, 0),
                       thickness=3)

        cv2.imshow("Matched contour points2", tmp_image)
        cv2.waitKey()
