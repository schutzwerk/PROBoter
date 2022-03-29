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

from typing import Iterable, Tuple, Optional

import cv2
import numpy as np

from pcb_analysis.model import Pin, Chip, ChipPackage


def draw_pin_detections(image: np.ndarray, pins: Iterable[Pin], color=(0, 0, 255),
                        marker_size=10, marker_thickness=1, draw_pin_contours=False,
                        fill_color=None) -> np.ndarray:
    """
    Draws the results of the pin detection

    :param image: The image to draw in
    :param pins: The detected chip pins
    :param color: The color that should be used to draw the pin markers
    :param marker_size: The size of the pin marker in pixel
    :param marker_thickness: The thickness of the pin marker lines in pixel
    :param draw_pin_contours: Whether to draw the detected pin contours
    :param fill_color: The fill color to draw the contour overlay. If is None
                       only the contour outline is drawn.
    :return: The modified image
    """
    line_width = 1
    for pin in pins:
        center = pin.center.tolist()
        center_p = (int(center[0]), int(center[1]))
        image = draw_crosshair(image=image,
                               point=center_p,
                               size=marker_size,
                               thickness=marker_thickness,
                               color=color)

        if draw_pin_contours:
            if fill_color is not None:
                image = draw_contour_overlay(image=image,
                                             contours=pin.contour,
                                             contour_color=fill_color,
                                             outline_thickness=line_width,
                                             outline_color=color)
            else:
                image = cv2.drawContours(
                    image, pin.contour, -1, color, line_width)

    return image


def draw_chip_detections(image: np.ndarray, chips: Iterable[Chip],
                         line_width: int = 5, color: Tuple[int, int, int] = (0, 0, 255),
                         alpha: float = 0.2, fill: bool = True) -> np.ndarray:
    """
    Draw chip detection results

    :param image: Image in which the detections should be drawn to
    :type image: np.ndarray
    :param predictions: Iterable of detected chips
    :type predictions: Iterable[Chip]
    :param line_width: Line width of the bounding box which is drawn
                       arround each prediction, defaults to 5
    :type line_width: int, optional
    :param color: Fill color of the prediction area, defaults to (0, 0, 255)
    :type color: Tuple[int, int, int], optional
    :param alpha: Alpha value / transparency of the prediction fill area, defaults to 0.2
    :type alpha: float, optional
    :param fill: Whether to fill the prediction area, defaults to True
    :type fill: bool, optional
    :return: The modified image
    :rtype: np.ndarray
    """

    # Convert the bounding boxes
    bboxes = [np.int0(np.reshape(chip.bbox, (4, 2, 1))) for chip in chips]

    if fill:
        # Draw an overlay
        image = draw_contour_overlay(image, bboxes, color, alpha,
                                     outline_thickness=line_width)
    else:
        # Only draw the outlines
        image = cv2.drawContours(image, bboxes, -1, color, line_width)

    # Draw the labels and confidences
    font_face = cv2.FONT_HERSHEY_PLAIN
    font_scale = 3
    font_thickness = 2
    text_padding = 15
    for i, bbox in enumerate(bboxes):
        text = "IC"
        if chips[i].package is not ChipPackage.UNKNOWN:
            text += f" ({chips[i].package.value})"
        conf = chips[i].confidence
        text += f": {conf * 100:.0f}%"
        text_size = cv2.getTextSize(
            text, font_face, font_scale, font_thickness)
        # Text centering
        bbox_min_x = bbox[:, 0].min()
        bbox_min_y = bbox[:, 1].min()
        # Draw the text box
        image = cv2.rectangle(img=image,
                              pt1=(bbox_min_x, bbox_min_y),
                              pt2=(bbox_min_x + text_size[0][0]
                                   + 2 * text_padding, bbox_min_y
                                   - (text_size[0][1] + 2 * text_padding)),
                              color=color,
                              thickness=cv2.FILLED)
        # Draw the label and confidence
        image = cv2.putText(image,
                            text,
                            # Origin
                            (bbox_min_x + text_padding,
                             bbox_min_y - text_padding),
                            font_face,
                            font_scale,
                            (255, 255, 255),
                            font_thickness,
                            8)
    return image


def draw_crosshair(image: np.ndarray, point: np.ndarray,
                   size: int = 5, thickness: int = 1,
                   color: Tuple[int, int, int] = (0, 0, 255)) -> np.ndarray:
    """
    Draws a crosshair in an image
    :param image: The image to draw in
    :type image: np.ndarray
    :param point: The location where the crosshair will be drawn
    :type point: np.ndarray
    :param size: The crosshair size in pixel
    :type size: int
    :param thickness: The crosshair line thickness in pixel
    :type thickness: int
    :param color: The crosshair color
    :type color: Tuple[int, int, int]
    :return: The modified image
    :rtype: np.ndarray
    """
    half_size = int(0.5 * size)
    ch_points = ((point[0] + half_size, point[1]),
                 (point[0] - half_size, point[1]),
                 (point[0], point[1] + half_size),
                 (point[0], point[1] - half_size))

    # Draw the crosshair
    for ch_point in ch_points:
        pt1 = point
        pt2 = limit_point(ch_point, image.shape[1], image.shape[0])
        cv2.line(image, pt1, pt2, color, thickness)

    return image


def draw_contour_overlay(image: np.ndarray, contours: Iterable[np.ndarray],
                         contour_color: Tuple[int, int, int] = (0, 0, 255),
                         alpha: float = 0.5, outline_thickness: int = 1,
                         outline_color: Optional[Tuple[int, int, int]] = None) -> np.ndarray:
    """
    Draw filled contours as an overlay into in image

    :param image: The image to draw into
    :type image: np.ndarray
    :param contours: The contours to draw
    :type contours: Iterable[np.ndarray]
    :param contour_color: The color used to draw the contour overlay
    :type contour_color: Tuple[int, int, int]
    :param alpha: Value specifying how opaque the overlay should be
                  in the range of [0.0, 1.0]
    :type alpha: float
    :param outline_thickness: The line thickness used to draw the contour outlines in pixel
    :type outline_thickness: int
    :param outline_color: The color of the contour outlines. If None the same color as
                          the one specified with the parameter contour_color will be used
    :type outline_color: Tuple[int, int, int]
    :return: The image with contour overlay
    :rtype: np.ndarray
    """
    overlay = np.zeros(image.shape, dtype=np.uint8)
    overlay = cv2.drawContours(
        overlay, contours, -1, contour_color, cv2.FILLED)
    mask = np.zeros(image.shape, dtype=np.uint8)
    mask = cv2.drawContours(mask, contours, -1, (255, 255, 255), cv2.FILLED)
    masked_image = cv2.addWeighted(image, 1 - alpha, overlay, alpha, 0.0)
    np.copyto(image, masked_image, where=np.greater(mask, 1))

    if outline_thickness > 0:
        if outline_color is None:
            outline_color = contour_color
        image = cv2.drawContours(
            image, contours, -1, outline_color, outline_thickness)

    return image


def limit_point(point: Tuple[int, int], width: int, height: int) -> Tuple[int, int]:
    """
    Limit a point to the image size

    :param point: The point to adjust as a tuple of (x, y)
    :type point: Tuple[int, int]
    :param width: The image width in pixel
    :type width: int
    :param height: The image height in pixel
    :type height: int
    :return: The limited point. Coordinates less than zero are set to 0
             and coordinates that exceed the image dimensions are set
             to the max. image dimensions
    :rtype: Tuple[int, int]
    """
    return (max(0, min(point[0], width - 1)),
            max(0, min(point[1], height - 1)))
