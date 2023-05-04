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

from abc import abstractmethod
import numpy as np

from .camera import Camera


class MovableCamera(Camera):
    """
    A camera that is mounted on a moving
    two-axes slide system
    """

    @abstractmethod
    async def home(self) -> None:
        """
        Home all axes
        """

    @abstractmethod
    async def move(self, position: np.ndarray, feed: float = 1000,
                   raise_z: bool = True) -> None:
        """
        Move the camera to a given position

        This is an UNSAFE command! Collision avoidance is not active here. So
        use with caution.

        :param position: Position the camera should be moved to as
                         numpy 2D vector. The position is in the local axes
                         controller system!
        :type position: np.ndarray
        :param feed: Movement feed in mm/min, defaults to 1000
        :type feed: float
        :param raise_z: Whether to raise the Z axis before the movement in
                        the XY plane
        :type raise_z: bool
        """

    @abstractmethod
    async def move_to_bring_point_into_view(self, ref_point: np.ndarray,
                                            image_point: np.ndarray,
                                            clear_z: bool = True,
                                            feed: float = 300) -> None:
        """
        Move the camera so that a given point in the reference system
        becomes visible at a defined location in the camera view

        :param ref_point: The reference point to bring into view as
                          numpy 3D vector
        :param image_point: The point in the camera view where the reference
                            point shall be visible
        :param clear_z: Whether to move the z-axis to it's origin before
                        moving in the xy-plane
        :param feed: The axes feed in mm/min
        """

    @abstractmethod
    def calc_axes_position(self, ref_point: np.ndarray, image_point: np.ndarray) \
            -> np.ndarray:
        """
        Calculate the axes coordinates so that a given point in the
        reference coordinate system is visible at a particular position
        in the camera image

        :param ref_point: The point in the reference coordinate system as
                          numpy 3D vector
        :param image_point: The point in the image plane as numpy 2D vector
        :return: The axes coordinates so that the ref_point and image point
                 matches as numpy 3D vector
        """
