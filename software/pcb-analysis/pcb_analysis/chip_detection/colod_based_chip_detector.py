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

from typing import Iterable, Dict, Any

import cv2
import numpy as np

from pcb_analysis.model import Chip

from .chip_detector import ChipDetector


class ColorBasedChipDetector(ChipDetector):
    """
    A chip detector that uses color thresholding and contour finding
    to detect chips on images of populated PCBs.
    """

    # Default threshold for chip detection based on experiments
    DEFAULT_CHIP_THRESHOLD = {"color-space": "hsv",
                              "min": (0, 0, 0),
                              "max": (50, 95, 110)}

    def __init__(self, thresholds: Dict[str, Any] = None, min_chip_size: int = 300):
        """
        Initialize the detector with a given set of color thresholds

        :param thresholds: A list of color thresholds used for image binarization
        :type thresholds: Dict[str, Any]
        :param min_chip_size: The minimal chip size in pixel.
                              Only regions which are in both dimensions width and
                              height greater than that value are returned.
        :type min_chip_size: int
        """
        # The thresholds used for image binarization
        self.thresholds = thresholds
        if self.thresholds is None:
            self.thresholds = [self.DEFAULT_CHIP_THRESHOLD]
        # The minimum chip dimensions
        self.min_chip_size = min_chip_size

    def detect_chips(self, image: np.ndarray) -> Iterable[Chip]:
        """
        Perform chip detection

        :param image: Colored PCB image
        :type image: np.ndarray
        :return: The detected chip contours
        :rtype: Iterable[Chip]
        """
        # Blur the image to remove image noise
        blurred_img = cv2.blur(image, ksize=(5, 5))

        # Apply color thresholding
        for threshold in self.thresholds:
            converted_image = blurred_img
            if threshold['color-space'].lower() == 'lab':
                converted_image = cv2.cvtColor(blurred_img, cv2.COLOR_BGR2LAB)
            elif threshold['color-space'].lower() == 'hsv':
                converted_image = cv2.cvtColor(blurred_img, cv2.COLOR_BGR2HSV)
            binary_img = cv2.inRange(converted_image,
                                     np.array(threshold['min']),
                                     np.array(threshold['max']))

        # Cleanup the results using morphological operations
        kernel = np.ones((5, 5), np.uint8)
        eroded_img = cv2.morphologyEx(
            binary_img, cv2.MORPH_OPEN, kernel, iterations=3)

        # Contour finding
        contours, _ = cv2.findContours(
            eroded_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Rectangle fitting
        chip_detections = []
        for contour in contours:
            rect = cv2.minAreaRect(contour)
            width = rect[1][0]
            height = rect[1][1]

            # Filter by min. chip size
            if width >= self.min_chip_size and height >= self.min_chip_size:
                chip_detections.append(
                    Chip(confidence=1.0,
                         bbox=cv2.boxPoints(rect).reshape(4, 2)))

        return chip_detections
