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
from typing import Tuple, Iterable

import cv2
import numpy as np


# Allow single character variable names to improve readability in mathematical formulas
# pylint: disable=invalid-name
class LinearAlgebra:
    """
    Collection of solutions to common
    algebraic problems
    """

    logger = logging.getLogger(__module__)

    @staticmethod
    def to_homogenous(points: Iterable[float]) -> Iterable[float]:
        """
        Converts a given tuple representing coordinates in Eucledian
        space to homogeneous space by appending an additional dimension
        with value 1

        :param points: The points in Eucledian space to convert
        :type points: Iterable[float]
        :return: The point in homogeneous coordinate space
        :rtype: Iterable[float]
        """
        return cv2.convertPointsToHomogeneous(np.array([points]))[0]

    @staticmethod
    def calculate_base_change(p_b1: np.ndarray, p_b2: np.ndarray) \
            -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates the base change matrix from a given set of 3D
        point correspondences in two different coordinate systems.

        T x p_b1 = p_b2

        The transformation takes also into account the coordinate
        system offsets.

        :param p_b1: 3D points in the fist coordinate system as
                     n x 3 numpy array
        :param p_b2: 3D points in the second / target coordinate system
                     as n x 3 numpy array
        :return: A tuple of:
                - The 4 x 4 transformation matrix from base 1 to base 2
                - The residuals
        """

        n = p_b1.shape[0]
        m = p_b2.shape[0]

        if n != m:
            raise ValueError("The number of points are not the same")

        # Calculate the base change by minimizing the error in the equation
        # a x V = b
        a = np.zeros((3 * n, 12))
        b = np.zeros(3 * n)
        for i in range(n):
            a[i * 3, 0:3] = p_b1[i, :]
            a[i * 3 + 1, 3:6] = p_b1[i, :]
            a[i * 3 + 2, 6:9] = p_b1[i, :]

            a[i * 3, 9] = 1.0
            a[i * 3 + 1, 10] = 1.0
            a[i * 3 + 2, 11] = 1.0

            b[i * 3: (i + 1) * 3] = p_b2[i, :]

        x, residuals, _, __ = np.linalg.lstsq(a, b, rcond=None)

        # Rebuild the transformation matrix
        tmat = np.eye(4)
        tmat[0:3, 0:3] = x[0:9].reshape(3, 3)
        tmat[0:3, 3] = x[9:12]

        # Calculate the residuals
        residuals = np.zeros(p_b1.shape)
        for i in range(p_b1.shape[0]):
            t_1 = np.ones(4)
            t_1[0:3] = p_b1[i, :]
            residuals[i, :] = p_b2[i, :] - np.matmul(tmat, t_1)[0:3]

        return tmat, residuals

    @classmethod
    def calculate_base_change_2d(cls, p_b1, p_b2):
        """
        Calculates the base change matrix from a given set of 2D
        point correspondences in two different coordinate systems.

        T x p_b1 = p_b2

        The transformation takes also into account the coordinate
        system offsets.

        :param p_b1: 2D points in the fist coordinate system as
                     n x 2 numpy array
        :param p_b2: 2D points in the second / target coordinate system
                     as n x 2 numpy array
        :return: A tuple of:
                - The 3 x 3 transformation matrix from base 1 to base 2
                - The residuals
        """

        n = p_b1.shape[0]
        m = p_b2.shape[0]

        if n != m:
            raise ValueError("The number of points are not the same")

        # Calculate the base change by minimizing the error in the equation
        # a x V = b
        a = np.zeros((2 * n, 6))
        b = np.zeros(2 * n)
        for i in range(n):
            a[i * 2, 0:2] = p_b1[i, :]
            a[i * 2 + 1, 2:4] = p_b1[i, :]

            a[i * 2, 4] = 1.0
            a[i * 2 + 1, 5] = 1.0

            b[i * 2: (i + 1) * 2] = p_b2[i, :]

        x, residuals, rank, _ = np.linalg.lstsq(a, b, rcond=None)

        if rank < 6:
            cls.logger.warning(("Rank of matrix too small (%d/%d). "
                                "Solution may be inaccurate!"), rank, 6)

        # Rebuild the transformation matrix
        tmat = np.eye(3)
        tmat[0:2, 0:2] = x[0:4].reshape(2, 2)
        tmat[0:2, 2] = x[4:6]

        # Calculate the residuals
        residuals = np.zeros(p_b1.shape)
        for i in range(p_b1.shape[0]):
            t_1 = np.ones(3)
            t_1[0:2] = p_b1[i, :]
            residuals[i, :] = p_b2[i, :] - np.matmul(tmat, t_1)[0:2]

        return tmat, residuals
