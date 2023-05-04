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

from dataclasses import dataclass, field

import numpy as np
from scipy import optimize


@dataclass
class CircleFitResult:
    """
    Result of circle fit operation
    """
    # The fitted circle center as numpy 2D vector
    center: np.ndarray = field(default_factory=lambda: np.zeros(2))
    # The fitted circle radius
    radius: float = 0.0
    # The residuals of the fitted points as (nx2) numpy array
    residuals: np.ndarray = field(default_factory=lambda: np.zeros(1, 2))


class CircleFit:
    """
    Various algorithms to solve the 2D circle fit problem
    """

    @staticmethod
    def fit_least_squares(x: np.ndarray, y: np.ndarray) -> CircleFitResult:
        """
        Source taken from http://www.scipy.org/Cookbook/Least_Squares_Circle
        and slightly modified.

        :param x: 1D vector containing the X coordinates of the 2D points to fit
        :type x: np.ndarray
        :param y: 1D vector containing the Y coordinates of the 2D points to fit
        :type y: np.ndarray
        :return: Circle fit results
        :rtype CircleFitResult
        """

        def calc_r(center_x, center_y):
            """
            Calculate the distance of each 2D points
            from the center (xc, yc)
            """
            return np.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)

        def f_2(center):
            """
            Calculate the algebraic distance between the data points
            and the mean circle centered at center=(xc, yc)
            """
            r_i = calc_r(*center)
            return r_i - r_i.mean()

        # coordinates of the barycenter
        x_m = np.mean(x)
        y_m = np.mean(y)

        # optimize the circle center
        center_estimate = x_m, y_m
        center_2, _ = optimize.leastsq(f_2, center_estimate)

        ri_2 = calc_r(*center_2)
        r_2 = ri_2.mean()
        residu_2 = sum((ri_2 - r_2) ** 2)

        return CircleFitResult(center=center_2,
                               radius=r_2,
                               residuals=residu_2)
