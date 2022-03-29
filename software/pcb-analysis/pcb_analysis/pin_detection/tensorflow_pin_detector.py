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
from os.path import join, dirname
from typing import Iterable

import numpy as np

from pcb_analysis.model import Pin
from pcb_analysis.utils import TensorflowDetector

from .pin_detector import PinDetector


class TensorflowPinDetector(PinDetector, TensorflowDetector):
    """
    A detector that uses the popular Tensorflow library
    to perform pin detection.
    """

    # The directory with the trained models.
    MODEL_DIR = join(dirname(__file__), '../tf_models')

    FASTER_RCNN_IC_PINS = "faster_rcnn_inception_resnet_v2_atrous-ic_pins-16021"

    MODELS = [FASTER_RCNN_IC_PINS]

    # Mapping from numeric labels to string labels
    LABEL_DICT = {
        1: 'pin'
    }

    logger = logging.getLogger(__module__)

    def __init__(self, model: str = FASTER_RCNN_IC_PINS,
                 conf_threshold: float = 0.5):
        """

        :param model: The trained model to use
        :type model: str
        :param conf_threshold Threshold of the confidence value. Only
                              detections with a confidence value of
                              at least the given value are returned.
        :type conf_threshold: float
        """
        PinDetector.__init__(self)
        TensorflowDetector.__init__(self, model_file=join(self.MODEL_DIR, model + ".pb"),
                                    conf_threshold=conf_threshold)

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
        detections = self.detect(chip_image, self.LABEL_DICT)
        pins = self.contours_to_pin_results([d['bbox'] for d in detections])
        return pins

    def release(self) -> None:
        """
        Free all resources allocated by the Tensorflow session
        """
        TensorflowDetector.release(self)
