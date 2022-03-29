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
import pytesseract
import numpy as np

from .chip_identifier import ChipIdentifier


class SimpleChipIdentifier(ChipIdentifier):
    """
    Chip identifier that tries to identify a chip
    by the printed marking on the ICs housing

    STILL WIP!!
    NOT WORKING YET!!
    """

    log = logging.getLogger(__module__)

    def read_chip_id(self, chip_image: np.ndarray) -> str:
        """
        Reads the chip id from the chip
        housing.

        NOT WORKING YET!!

        :param chip_image: Image of the chip housing
        :type chip_image: np.ndarray
        :return: A string containing the chip id
        :rtype: str
        """

        # Convert to gray scale image
        gray_img = cv2.cvtColor(chip_image, cv2.COLOR_BGR2GRAY)

        # Apply all further steps with
        # all possible rotations of the
        # chip
        for i in range(4):
            tmp = gray_img.copy()
            for _ in range(i):
                tmp = cv2.rotate(tmp, cv2.ROTATE_90_CLOCKWISE)

            # Binarization (works only with images with exact 2 colors!)
            _, edges = cv2.threshold(
                tmp, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Remove the small noise with erosion / dilation
            kernel = np.ones((3, 3), np.uint8)
            char_mask = cv2.morphologyEx(
                edges, cv2.MORPH_OPEN, kernel, iterations=2)

            # Find single character contours
            contours, _ = cv2.findContours(
                char_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if w > 30 and h > 30:
                    blurred_img = cv2.blur(char_mask, ksize=(5, 5))
                    char_img = blurred_img[y:y + h, x:x + w]

                    tmp_char = tmp.copy()
                    cv2.drawContours(tmp_char, contour, -1, (0, 255, 0), 3)

                    text = pytesseract.image_to_string(char_img)
                    self.log.info("'%s'", text)

                    cv2.namedWindow("chip", cv2.WINDOW_NORMAL &
                                    cv2.WINDOW_KEEPRATIO)
                    cv2.imshow("chip", char_img)
                    cv2.waitKey(-1)

            text = pytesseract.image_to_string(char_mask)
            self.log.info("angle(%f): '%s'", i * 90, text)

            cv2.namedWindow("chip", cv2.WINDOW_NORMAL & cv2.WINDOW_KEEPRATIO)
            cv2.imshow("chip", char_mask)
            cv2.waitKey(-1)

        return ""
