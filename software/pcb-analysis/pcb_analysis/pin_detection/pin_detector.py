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
from typing import Iterable, Tuple
from abc import ABC, abstractmethod

import cv2
import numpy as np

from pcb_analysis.model import Chip, Pin


class PinDetector(ABC):
    """
    Base class for pin detectors
    """

    logger = logging.getLogger(__module__)

    @staticmethod
    def extract_chips(board_image: np.ndarray, chip_detections: Iterable[Chip],
                      margin: int = 0) -> Iterable[Tuple[np.ndarray, np.ndarray]]:
        """
        Extract images of detected chips

        :param board_image: The PCB image
        :type: board_image: np.ndarray
        :param chip_detections: Chip detections as returned from ChipDetectors
        :chip_detections: Iterable[Chip]
        :param margin: Additional margin around the chip images
        :type margin: int
        :return: A tuple containing of:
                 - The extracted chip images as list of numpy arrays
                 - The chip offsets as n x 2 numpy array
        :rtype: Iterable[Tuple[np.ndarray, np.ndarray]]
        """
        chip_images = []
        offsets = np.zeros((len(chip_detections), 2))
        for i, chip in enumerate(chip_detections):
            bbox = chip.bbox
            min_x = int(bbox[:, 0].min()) - margin
            min_y = int(bbox[:, 1].min()) - margin
            max_x = int(bbox[:, 0].max()) + margin
            max_y = int(bbox[:, 1].max()) + margin

            # Range adjustment
            min_x = min(max(0, min_x), board_image.shape[1])
            max_x = max(0, min(board_image.shape[1], max_x))

            min_y = min(max(0, min_y), board_image.shape[0])
            max_y = max(0, min(board_image.shape[0], max_y))

            chip_img = board_image[min_y:max_y, min_x:max_x, :]
            chip_images.append(chip_img)
            offsets[i, :] = np.array((min_x, min_y))

        return chip_images, offsets

    @classmethod
    def contours_to_pin_results(cls, pin_contours: Iterable[np.ndarray]) -> Iterable[Pin]:
        """
        Create pins from contours by calculating the contour centers

        :param pin_contours: List of pin contours
        :type pin_contours: Iterable[np.ndarray]
        :return: List of pins as a list of dictionaries
        :rtype: Iterable[Pin]
        """
        # Summarize the pin results
        pins = []
        if pin_contours is not None:
            for contour in pin_contours:
                moments = cv2.moments(contour)
                if moments["m00"] == 0:
                    cls.logger.debug("Ignoring contour")
                else:
                    center_x = int(moments["m10"] / moments["m00"])
                    center_y = int(moments["m01"] / moments["m00"])
                    pins.append(Pin(center=np.array((center_x, center_y), float),
                                    contour=contour))

        return pins

    @abstractmethod
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

    def release(self) -> None:
        """
        Free all allocated resources
        """
