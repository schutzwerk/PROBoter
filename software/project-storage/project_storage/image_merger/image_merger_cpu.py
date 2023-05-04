# Copyright (C) 2022 SCHUTZWERK GmbH
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

import cv2
import numpy as np

from project_storage.model import PcbScan, PcbScanImage

from .image_merger import ImageMerger, ImageMergeException


class ImageMergerCpu(ImageMerger):
    """
    Simple image merger that utilizes only the CPU and
    therefore might be slow
    """

    log = logging.getLogger(__module__)

    def merge_scan(self, scan: PcbScan, resolution: float,
                   default_background=(128, 128, 128)) -> np.ndarray:
        """
        Generate a merged image bases on multiple PCB scan images

        The size of the final image is calculated as follows:
        width = <scan range in x> / resolution
        height = <scan range in y> / resolution

        @param scan: The PCB scan to merge
        @param resolution: The resolution of the final image in
                           millimeters per pixel
        @param default_background: The default background color as
                                   tuple of RGB values in the range
                                   of [0, 255] (uint values)
        """
        # Input validation
        if len(scan.images) > 1:
            raise ImageMergeException("Only singe image scans are supported")

        # Calculate the size of the final image
        img_width = int((scan.width) / resolution)
        img_height = int((scan.height) / resolution)
        self.log.debug('Final image size: %dx%d', img_width, img_height)

        if len(scan.images) < 1:
            self.log.warning("No scan images to merge. "
                             "Generating default image")
            return np.zeros((img_width, img_height, 3), np.uint8)

        # Calculate the corner coordinates of the specified scan area
        edge_points_global = np.array([[scan.x_max, scan.y_max, scan.z_offset],
                                       [scan.x_max, scan.y_min, scan.z_offset],
                                       [scan.x_min, scan.y_min, scan.z_offset],
                                       [scan.x_min, scan.y_max, scan.z_offset]])

        # Map the scan area corner coordinates to image coordinates
        scan_image: PcbScanImage = scan.images[0]
        edge_points_imgage = self._map_global_to_image_points(scan_image.camera_matrix,
                                                              scan_image.tmat,
                                                              edge_points_global)

        # Calculate the homography that describes the transformation
        # from image coordinates to global coordinates
        edge_points_final_img = np.array([[0, 0],
                                          [0, img_height],
                                          [img_width, img_height],
                                          [img_width, 0]], dtype=np.int32)

        homography, _ = cv2.findHomography(edge_points_imgage,
                                       edge_points_final_img)

        # Finally create the transformed image for the specified scan area
        merged_image = cv2.warpPerspective(np.copy(scan_image.image_data),
                                           homography,
                                           (img_width, img_height))
        return merged_image

    @classmethod
    def _map_global_to_image_points(cls, camera_matrix: np.ndarray,
                                    tmat_camera: np.ndarray,
                                    global_points: np.ndarray) -> np.ndarray:
        """
        Transform points from the global reference system to the image plane

        :param camera_matrix: Camera matrix as (3 x 3)
        :type camera_matrix: np.ndarray
        :param tmat_camera: Camera transformation matrix (4 x 4)
        :type tmat_camera: np.ndarray
        :param global_points: The points in the global reference system to
                              transform as n x 3 array
        :type global_points: np.ndarray
        :return: The corresponding points in the image plane as n x 2 array
        :rtype: np.ndarray
        """
        # Extend the given global points
        glob_points_ext = np.ones((global_points.shape[0], 4))
        glob_points_ext[:, :3] = global_points

        # Reduction matrix (3x4)
        tmat_red = np.eye(4)
        tmat_red = tmat_red[0:3, :]

        # Build the full transformation matrix
        tmat = np.linalg.inv(tmat_camera).T
        tmat = np.matmul(tmat_red, tmat)
        tmat = np.matmul(np.linalg.inv(camera_matrix), tmat)

        img_points = np.matmul(tmat, glob_points_ext.T).T
        img_points /= np.repeat(img_points[:, 2], 3).reshape(-1, 3)
        img_points = img_points[:, :2]

        return img_points.astype(np.int32)
