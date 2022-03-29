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
from os.path import join, dirname

import numpy as np

from pcb_analysis.model import Chip, ChipType, ChipPackage
from pcb_analysis.utils import TensorflowDetector

from .chip_detector import ChipDetector


class TensorflowChipDetector(ChipDetector, TensorflowDetector):
    """
    A detector that uses the popular Tensorflow library
    to perform chip detection.
    """

    # The directory with the trained models.
    MODEL_DIR = join(dirname(__file__), '../tf_models')

    SSD_PCB_CUSTOM = "ssd-pcb_custom-30628"
    FASTER_RCNN_PCB_CUSTOM = "faster_rcnn_inception_resnet_v2_atrous-pcb_custom-28162"

    MODELS = [SSD_PCB_CUSTOM,
              FASTER_RCNN_PCB_CUSTOM]

    # Mapping from numeric labels to string labels
    LABEL_DICT = {
        1: ChipPackage.UNKNOWN,
        2: ChipPackage.SON,
        3: ChipPackage.SOP,
        4: ChipPackage.QFN,
        5: ChipPackage.QFP,
        6: ChipPackage.BGA,
        7: ChipPackage.THT,
        8: ChipType.CONNECTOR_SMD,
        9: ChipType.CONNECTOR_THT,
        10: ChipType.IC_UNPOPULATED
    }

    logger = logging.getLogger(__module__)

    def __init__(self, model: str = FASTER_RCNN_PCB_CUSTOM, conf_threshold: float = 0.7):
        """
        Initialize a TensorfFlow-powered chip detector

        :param model: The trained model to use
        :type model: str
        :param conf_threshold Threshold of the confidence value. Only
                              detections with a confidence value of
                              at least the given value are returned.
        :type conf_threshold: float
        """
        ChipDetector.__init__(self)
        model_file = join(self.MODEL_DIR, model + ".pb")
        self.logger.info("Using chip detector model %s", model_file)
        TensorflowDetector.__init__(self, model_file=model_file,
                                    conf_threshold=conf_threshold)

    def detect_chips(self, image: np.ndarray) -> Iterable[Chip]:
        """
        Searches for chips in a given PCB image.

        :param image: The PCB image as numpy array. The image must
                      be a color image with 3 channels in BGR format!
        :return: An iterable collection of the detected chips.
        """
        detections = self.detect(image, self.LABEL_DICT)
        # Generate chip detections only for ICs (at the moment)!
        chips = [Chip(package=d['type'],
                      confidence=d['conf'],
                      bbox=d['bbox'])
                 for d in detections
                 if isinstance(d['type'], ChipPackage)]
        return chips

    def release(self):
        """
        Free all allocated resources
        """
        TensorflowDetector.release(self)
