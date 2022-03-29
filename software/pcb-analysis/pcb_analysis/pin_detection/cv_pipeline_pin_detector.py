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
from dataclasses import dataclass

import cv2
import numpy as np

from pcb_analysis.model import Pin
from pcb_analysis.utils import draw_contour_overlay, draw_pin_detections

from .pin_detector import PinDetector


@dataclass
class CvPipelinePinDetectorConfig:
    """
    Configuration of a CV pipeline pin detector
    """
    # The threshold value used in the distance map
    distance_threshold = 0.275
    # The relative size of the kernel used for the morphological
    # operations in percentage of the chip margin
    morph_kernel_size = 0.075
    # The size of the image area to use for chip package removal
    # with the flood filling algorithm
    chip_center_size = 0.5
    #  The +- offsets in each color channel that is used for
    # the flood filling algorithm used in the background removal
    background_offset = 40
    # The +- offsets in each color channel that is used for
    # the flood filling algorithm used in the chip package removal
    chip_package_offset = 5
    # The minimal contour size in pixels that a pin contour must have
    min_contour_size = 10
    # The number of opening operations to clean up prior to pin contour finding
    num_opening_ops = 3
    # Threshold for the binarization step before isolating the individual pins
    gray_threshold = 100
    # Whether to use morphological operations in the border regions to improve
    # pin separation
    use_border_region_morph_ops = True
    # Whether to use a threshold filter after the distance transform operation
    use_distance_transform_filter = True
    # Whether morphological operations shall be used during IC package removal
    use_morph_ops_for_package_removal = False


class CvPipelinePinDetector(PinDetector):
    """
    A pin detector that uses OTSU thresholding and
    contour finding to locate chip pins.
    """
    CHIP_BORDER_LEFT = 0
    CHIP_BORDER_RIGHT = 1
    CHIP_BORDER_TOP = 2
    CHIP_BORDER_BOTTOM = 3
    CHIP_BORDER_REGIONS = (CHIP_BORDER_LEFT,
                           CHIP_BORDER_RIGHT,
                           CHIP_BORDER_TOP,
                           CHIP_BORDER_BOTTOM)

    logger = logging.getLogger(__module__)

    def __init__(self, config: CvPipelinePinDetectorConfig = CvPipelinePinDetectorConfig(),
                 debug: bool = False):
        """
        Initialize a CV pipeline pin detector

        :param config: CV pipeline pin detector configuration
        :type config: CvPipelinePinDetectorConfig
        :param debug: Whether to show intermediate results for debugging
        :type debug: bool
        """
        self.config = config
        self.debug = debug
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

        # Blur the input image
        chip_image = cv2.bilateralFilter(chip_image, 9, 75, 75)

        # Remove the background and chip package
        bg_mask, chip_without_bg = self._remove_background(chip_image)
        package_mask, _ = self._remove_chip_package(chip_image)
        chip_image_without_bg = cv2.subtract(chip_image, bg_mask)
        chip_image_without_bg_and_pk = cv2.subtract(
            chip_image_without_bg, package_mask)

        # Apply thresholding to the remaining gray scale image
        gray = cv2.cvtColor(chip_image_without_bg_and_pk, cv2.COLOR_BGR2GRAY)
        _, thresh_gray = cv2.threshold(
            gray, self.config.gray_threshold, 255, cv2.THRESH_BINARY)

        # Separate the pins in the border regions with oriented morph. ops
        if self.config.use_border_region_morph_ops:
            pin_contour_mask = np.zeros(thresh_gray.shape, dtype=np.uint8)
            for region in self.CHIP_BORDER_REGIONS:
                pin_contour_mask = cv2.add(src1=pin_contour_mask,
                                           src2=self._find_pins_in_border_region(
                                               binary_chip_image=thresh_gray,
                                               chip_region=region))
        else:
            pin_contour_mask = thresh_gray

        # Optional distance transform to get the pin centers
        if self.config.use_distance_transform_filter:
            dist = cv2.distanceTransform(src=pin_contour_mask,
                                         distanceType=cv2.DIST_C,
                                         maskSize=3)
            if dist.max() > 0:
                dist = dist / dist.max()

            # Get only the strongest centers
            _, dist_thresholded = cv2.threshold(src=dist,
                                                thresh=self.config.distance_threshold,
                                                maxval=1.0,
                                                type=cv2.THRESH_BINARY)
            dist_thresholded = dist_thresholded.astype(np.uint8) * 255
        else:
            dist_thresholded = pin_contour_mask

        # Final contour finding
        merged_pin_contours, _ = cv2.findContours(
            dist_thresholded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

        # Summarize the pin results
        pins = self.contours_to_pin_results(merged_pin_contours)

        if self.debug:
            cv2.imshow("Original image", chip_image)
            cv2.imshow("Without background", chip_without_bg)
            cv2.imshow("Without background and package",
                       chip_image_without_bg_and_pk)
            cv2.imshow("Gray", gray)
            cv2.imshow("Gray thresholded", thresh_gray)
            cv2.imshow("Morph. cleaned", pin_contour_mask)
            cv2.imshow("Distances", dist)
            cv2.imshow("Distances thresholded", dist_thresholded)
            cv2.imshow("Pin contours", draw_contour_overlay(chip_image.copy(),
                                                            merged_pin_contours,
                                                            contour_color=(255, 0, 0)))
            cv2.imshow("Pin centers", draw_pin_detections(chip_image.copy(),
                                                          pins,
                                                          color=(0, 0, 255),
                                                          marker_thickness=1))
            cv2.waitKey()

        return pins

    def _find_pins_in_border_region(self, binary_chip_image, chip_region):

        # Extract the border region
        limits = [0, 0, 0, 0]
        if chip_region == self.CHIP_BORDER_TOP:
            limits = [0, self.chip_margin, 0, -1]
        elif chip_region == self.CHIP_BORDER_BOTTOM:
            limits = [-self.chip_margin, -1, 0, -1]
        elif chip_region == self.CHIP_BORDER_LEFT:
            limits = [0, -1, 0, self.chip_margin]
        elif chip_region == self.CHIP_BORDER_RIGHT:
            limits = [0, -1, -self.chip_margin, -1]
        region = binary_chip_image[limits[0]:limits[1], limits[2]:limits[3]]

        # Setup the kernel for the morphological operations
        kernel_long_side = int(
            self.config.morph_kernel_size * self.chip_margin)
        kernel_short_side = 1
        if chip_region in (self.CHIP_BORDER_TOP, self.CHIP_BORDER_BOTTOM):
            kernel = np.ones((kernel_long_side, kernel_short_side), np.uint8)
        else:
            kernel = np.ones((kernel_short_side, kernel_long_side), np.uint8)

        # Perform the morphological operations
        region_dil = region.copy()
        for _ in range(self.config.num_opening_ops):
            region_dil = cv2.morphologyEx(region_dil, cv2.MORPH_CLOSE, kernel)

        mask = np.zeros(binary_chip_image.shape, np.uint8)
        mask[limits[0]:limits[1], limits[2]:limits[3]] = region_dil

        return mask

    def _remove_background(self, chip_image):
        """
        Remove the background of a chip image

        :param chip_image: Colored chip image
        :return: A tuple containing:
                 - The binary mask of the background region
                 - The chip image without the background regions
        """

        # Use flood filling to create a mask that contains the
        # background region
        mask = np.zeros(
            (chip_image.shape[0] + 2, chip_image.shape[1] + 2), np.uint8)
        num_pixel_rows = 1
        seed_points = [(j, i) for i in range(chip_image.shape[0])
                       for j in range(num_pixel_rows)]
        seed_points += [(chip_image.shape[1] - (1 + j), i)
                        for i in range(chip_image.shape[0])
                        for j in range(num_pixel_rows)]
        seed_points += [(i, j) for i in range(chip_image.shape[1])
                        for j in range(num_pixel_rows)]
        seed_points += [(i, chip_image.shape[0] - (1 + j))
                        for i in range(chip_image.shape[1])
                        for j in range(num_pixel_rows)]
        for seed_point in seed_points:
            flags = 4  # connectivity
            flags |= cv2.FLOODFILL_MASK_ONLY
            flags |= cv2.FLOODFILL_FIXED_RANGE
            flags |= (255 << 8)  # 255 = fill value
            offset = self.config.background_offset
            lower_bound = (offset, offset, offset)
            upper_bound = (offset, offset, offset)
            _, _, mask, _ = cv2.floodFill(chip_image, mask,
                                          seed_point,
                                          (255, 0, 0),
                                          lower_bound,
                                          upper_bound,
                                          flags)

        # Remove flood filling padding
        mask = mask[1:-1, 1:-1]
        mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR)

        if self.debug:
            cv2.imshow("Background mask", mask)

        return mask, cv2.subtract(chip_image, mask)

    def _remove_chip_package(self, chip_image):
        """
        Remove the chip package from a chip image

        :param chip_image: Colored chip image
        :return: A tuple containing:
                 - The binary mask of the chip package region
                 - The chip image without the chip package
        """
        # Extract the image width and height
        h, w, _ = chip_image.shape

        # Use flood filling to create a mask that
        # contains only the chip package.
        # Assumption: The chip package center is in
        # the middle of the image
        mask = np.zeros((chip_image.shape[0] + 2,
                         chip_image.shape[1] + 2), np.uint8)
        chip_center_width = int(w * self.config.chip_center_size)
        chip_center_height = int(h * self.config.chip_center_size)
        seed_points = [(x, y) for y in range(int(0.5 * (h - chip_center_height)),
                                             int(0.5 * (h + chip_center_height)))
                       for x in range(int(0.5 * (w - chip_center_width)),
                                      int(0.5 * (w + chip_center_width)))]
        for seed_point in seed_points:
            flags = 4  # connectivity
            flags |= cv2.FLOODFILL_MASK_ONLY
            flags |= cv2.FLOODFILL_FIXED_RANGE
            flags |= (255 << 8)  # 255 = fill value
            offset = self.config.chip_package_offset
            _, _, mask, _ = cv2.floodFill(chip_image, mask,
                                          seed_point,
                                          (255, 0, 0),
                                          # Lower bound
                                          (offset, offset, offset),
                                          # Upper bound
                                          (offset, offset, offset),
                                          flags)

        # Remove flood filling padding
        mask = mask[1:-1, 1:-1]

        if self.config.use_morph_ops_for_package_removal:
            # Perform the morphological operations
            kernel = np.ones((7, 7), np.uint8)
            region_dil = mask.copy()
            for _ in range(3):
                region_dil = cv2.morphologyEx(
                    region_dil, cv2.MORPH_CLOSE, kernel, iterations=2)

            # Only use the outermost contour
            chip_package_contour, _ = cv2.findContours(
                region_dil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            new_mask = np.zeros(mask.shape)
            new_mask = cv2.drawContours(
                new_mask, chip_package_contour, -1, 255, cv2.FILLED)
            new_mask = new_mask.astype(np.uint8)
        else:
            new_mask = mask

        # Required to subtract the mask from a colored image
        new_mask = cv2.cvtColor(new_mask, cv2.COLOR_GRAY2BGR)

        if self.debug:
            mask_inv = np.invert(new_mask)
            chip_package = cv2.subtract(chip_image, mask_inv)
            cv2.imshow("Chip package", chip_package)
            cv2.imshow("Chip package mask", mask)

        return new_mask, cv2.subtract(chip_image, new_mask)

    @staticmethod
    def _adjust_rectangle_dims(rect, width_delta=0, height_delta=0):
        """
        Changes an OpenCV Box2D width and height

        :param rect: The box to adjust
        :param width_delta: The width delta
        :param height_delta: The height delat
        :return: The modified box
        """
        return rect[0], (rect[1][0] + width_delta, rect[1][1] + height_delta), rect[2]
