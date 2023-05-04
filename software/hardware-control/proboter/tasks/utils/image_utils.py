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

import cv2
import numpy as np


class ImageUtils:
    """
    Provides a collection of useful methods
    for image handling
    """

    @staticmethod
    def show_image(title: str, image: np.ndarray,
                   wait_time: float = None) -> None:
        """
        Show an image in a separate window

        :param title: Title of the window
        :param image: The image data
        :param wait_time: Time to wait for a key press until the
                          function continues
        """
        cv2.namedWindow(title, cv2.WINDOW_NORMAL & cv2.WINDOW_KEEPRATIO)
        cv2.imshow(title, image)

        if wait_time is not None:
            cv2.waitKey(wait_time)

    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """
        Normalize an image. This includes subtraction
        of the average per color channel and normalizing
        the values in the range to fit in a range of
        0 ... 255.

        :param image: The image to normalize
        :return: The normalized image
        """

        # Change the type to float for further processing
        norm_img = image.astype(np.float)

        # Subtraction of the average
        avgs = np.mean(norm_img, axis=(0, 1))
        for i, avg in enumerate(avgs):
            norm_img[:, :, i] -= avg

        # Rescaling
        max_values = np.amax(norm_img, axis=(0, 1))
        min_values = np.amin(norm_img, axis=(0, 1))
        for i in range(len(avgs)):
            norm_img[:, :, i] -= min_values[i]
            norm_img[:, :, i] /= (max_values[i] - min_values[i])

        # Rescaling
        norm_img = norm_img * 255

        return norm_img.astype(np.uint8)

    @staticmethod
    def scale_to_max(image: np.ndarray, max_dim: int) -> np.ndarray:
        """
        Scales an image so that it's largest dimension
        has a defined value.

        :param image: The image to scale.
        :param max_dim: The size of the largest dimension after rescaling.
        :return: The rescaled image.
        """
        scale = max_dim / max(image.shape[0], image.shape[1])
        new_shape = (int(image.shape[1] * scale), int(image.shape[0] * scale))
        return cv2.resize(image, new_shape)
