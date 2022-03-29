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
from typing import Iterable

import cv2
import numpy as np

from pcb_analysis.model import ChipBorderRegion, Pin
from pcb_analysis.utils import draw_pin_detections

from .pin_detector import PinDetector


class ColorBasedPinDetector(PinDetector):
    """
    A pin detector based on color segmentation
    with global color thresholding.
    """

    logger = logging.getLogger(__module__)

    def __init__(self, hsv_threshold=((0, 0, 0), (255, 255, 255)), debug=False):
        self.debug = debug
        self.hsv_threshold = hsv_threshold
        self.distance_threshold = 0.25
        self.chip_margin = 0

    def find_chip_pins(self, chip_image: np.ndarray, chip_margin: int = 30) -> Iterable[Pin]:
        """
        Find pins in an chip image

        :param chip_image: Image that shows a chip with minimal
                           surrounding background
        :type chip_image: np.ndarray
        :param chip_margin: The space that was added to the chip contour
        :type chip_margin: int
        :return: An iterable collection of detected pins
        :rtype: Iterable[Pin]
        """

        self.chip_margin = chip_margin

        # Color thresholding in the HSV color space
        hsv_image = cv2.cvtColor(chip_image, cv2.COLOR_BGR2HSV)
        thresholded = cv2.inRange(
            hsv_image, self.hsv_threshold[0], self.hsv_threshold[1])

        # Use morphological operations to remove small contours
        kernel = np.ones((5, 5), np.uint8)
        thresholded_reduced = cv2.morphologyEx(
            thresholded, cv2.MORPH_CLOSE, kernel, iterations=2)

        # Detect pins in the four chip border regions
        pin_contours = []
        for region in ChipBorderRegion:
            pin_contours += self._find_pins_in_border_region(binary_chip_image=thresholded_reduced,
                                                             chip_region=region)

        # Unify pin contours
        mask = np.zeros(chip_image.shape, dtype=np.uint8)
        for contour in pin_contours:
            mask = cv2.drawContours(
                mask, [contour], -1, (255, 255, 255), cv2.FILLED)
        mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
        pin_contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        pins = self.contours_to_pin_results(pin_contours)

        if self.debug:
            cv2.imshow("Original image", chip_image)
            cv2.imshow("Thresholded", thresholded)
            cv2.imshow("Thresholded reduced", thresholded_reduced)
            cv2.imshow("Pin contours", draw_pin_detections(chip_image.copy(),
                                                           pins=pins,
                                                           draw_pin_contours=True))
            cv2.waitKey()

        return pins

    def _find_pins_in_border_region(self, binary_chip_image, chip_region):
        height, width = binary_chip_image.shape

        region = None
        if chip_region == ChipBorderRegion.TOP:
            region = binary_chip_image[0:self.chip_margin, 0:-1]
        elif chip_region == ChipBorderRegion.BOTTOM:
            region = binary_chip_image[-self.chip_margin:-1, 0:-1]
        elif chip_region == ChipBorderRegion.LEFT:
            region = binary_chip_image[0:-1, 0:self.chip_margin]
        elif chip_region == ChipBorderRegion.RIGHT:
            region = binary_chip_image[0:-1, -self.chip_margin:-1]

        kernel_long_side = int(0.2 * self.chip_margin)
        if chip_region in (ChipBorderRegion.TOP, ChipBorderRegion.BOTTOM):
            kernel = np.ones((kernel_long_side, 1), np.uint8)
        else:
            kernel = np.ones((1, kernel_long_side), np.uint8)
        region_dil = cv2.morphologyEx(
            region, cv2.MORPH_OPEN, kernel, iterations=2)
        pin_contours, _ = cv2.findContours(region_dil.astype(
            np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)

        self.logger.debug("%d possible pin contours found",
                          len(pin_contours))

        filtered_pin_contours = []
        for pin_contour in pin_contours:
            if pin_contour.shape[0] >= 10:
                filtered_pin_contours.append(pin_contour)

        self.logger.debug("%d pin contours found",
                          len(filtered_pin_contours))

        region_contours = cv2.cvtColor(region, cv2.COLOR_GRAY2BGR)
        region_contours = cv2.drawContours(
            region_contours, filtered_pin_contours, -1, (0, 0, 255), 1)

        # Adjust the found pin contours
        for filtered_pin_contour in filtered_pin_contours:
            if chip_region == ChipBorderRegion.BOTTOM:
                filtered_pin_contour[:, :, 1] += (height - self.chip_margin)
            elif chip_region == ChipBorderRegion.RIGHT:
                filtered_pin_contour[:, :, 0] += (width - self.chip_margin)

        return filtered_pin_contours
