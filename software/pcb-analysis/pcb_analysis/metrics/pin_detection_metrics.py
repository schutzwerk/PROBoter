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

import time
import logging
from dataclasses import dataclass, field
from typing import Iterable, Any

import cv2
import numpy as np

from pcb_analysis.model import Pin
from pcb_analysis.utils import draw_pin_detections


@dataclass
class SimpleMetricResults:
    """
    Simple detection metric results
    """
    true_positive_matches: Iterable[Any] = field(default_factory=list)
    false_positives: Iterable[Any] = field(default_factory=list)
    false_negatives: Iterable[Any] = field(default_factory=list)
    multiple_matches: Iterable[Any] = field(default_factory=list)
    tp_abs_distances: np.ndarray = field(default_factory=lambda: np.empty(0))
    tp_rbd: np.ndarray = field(default_factory=lambda: np.empty(0))
    mean_tp_rbd: float = 0

    @property
    def true_positives(self):
        """
        List of True Positives (TP)
        """
        return [p[0] for p in self.true_positive_matches]

    @property
    def precision(self) -> float:
        """
        Precision value according to the Pascal VOC metric
        """
        sum_detections = len(self.true_positives) + \
            len(self.false_positives) + len(self.multiple_matches)
        return (len(self.true_positives) / sum_detections) \
            if sum_detections > 0 else 0

    @property
    def recall(self) -> float:
        """
        Recall value according to the Pascal VOC metric
        """
        sum_detections = len(self.true_positives) + len(self.false_negatives)
        return (len(self.true_positives) / sum_detections) \
            if sum_detections > 0 else 0


@dataclass
class DatasetEvalMetricResults:
    """
    Detection metric summary for a whole image data set
    """
    num_false_positives: int = 0
    mean_rbd: float = 0.0
    mean_false_positives: float = 0.0
    mean_detection_time: float = 0.0
    mean_precision: float = 0.0
    mean_recall: float = 0.0

    def __str__(self):
        return ("***************************"
                "Dataset eval metric results:"
                "***************************"
                "False positives: {self.num_false_positives:d}"
                "Mean false positives per image: {self.mean_false_positives:.1f}"
                "Avg. RBD: { self.mean_rbd:.3f}"
                "Avg. precision: {self.mean_precision:3f}"
                "Avg. recall: {self.mean_recall:3f}"
                "Avg. detection time: {self.mean_detection_time:.3f}s")


class PinDetectionMetrics:
    """
    Metrics to evaluate and compare different pin detectors
    """

    # Colors for displaying the detection results
    COLOR_TRUE_POSITIVE = (0, 255, 0)
    COLOR_FALSE_POSITIVE = (0, 0, 255)
    COLOR_MUTLI_MATCH = (0, 255, 255)
    COLOR_GROUND_TRUTH = (255, 0, 0)

    logger = logging.getLogger(__module__)

    @classmethod
    def calculate_simple_metric(cls, pin_gt_boxes, detected_pins) -> SimpleMetricResults:
        """
        Calculate simple pin detection metric for a given set of
        ground truth pins and object detections

        :param pin_gt_boxes: Pin ground truth bounding boxes
        :param detected_pins: Iterable of pin detections
        :return: Calculated detection metric
        :rtype: SimpleMetricResults
        """
        pin_matches = {i: [] for i in range(len(pin_gt_boxes))}
        cls.logger.debug("%d Ground Truth pins", len(pin_gt_boxes))
        cls.logger.debug("%d detected pins:", len(detected_pins))

        # Match the detected pins to the ground truth pin boxes
        for i, pin in enumerate(detected_pins):
            for j, pin_gt in enumerate(pin_gt_boxes):
                pin_center = pin.get_center()
                if pin_gt[0] <= pin_center[0] <= pin_gt[2] \
                        and pin_gt[1] <= pin_center[1] <= pin_gt[3]:
                    pin_matches[j].append(i)

        all_matches = [item for sublist in list(
            pin_matches.values()) for item in sublist]
        true_positives = [(matched[0], i)
                          for i, matched in pin_matches.items() if len(matched) >= 1]
        multiple_matches = [mm for i, matched in pin_matches.items() if len(
            matched) > 1 for mm in matched[1:]]
        not_matched_gt = [
            i for i, matched in pin_matches.items() if len(matched) < 1]
        false_positives = [i for i in range(
            len(detected_pins)) if i not in all_matches]

        all_matches.sort()
        true_positives.sort(key=lambda v: v[0])
        multiple_matches.sort()
        not_matched_gt.sort()
        false_positives.sort()

        # Calculate the relative distances of the matched pins
        matched_pin_dist = np.zeros(len(true_positives))
        matched_dist_values = np.zeros(len(true_positives))
        for i, pin_match in enumerate(true_positives):
            # Calculate the GT center
            gt_box = pin_gt_boxes[pin_match[1]]
            pin = detected_pins[pin_match[0]]
            pin_gt_center = np.array(((gt_box[2] + gt_box[0]) * 0.5,
                                      (gt_box[3] + gt_box[1]) * 0.5))
            # Calculate the GT width and height
            pin_gt_wh = np.array((gt_box[2] - gt_box[0],
                                  gt_box[3] - gt_box[1]))

            pin_center = np.array((pin.get_center()[0], pin.get_center()[1]))

            # Calculate the distance from the GT center to the
            # actually detected pin center
            abs_dist = np.abs(pin_gt_center - pin_center)
            rel_abs_dist = abs_dist / (pin_gt_wh * 0.5)
            rel_abs_dist_inv = np.ones(2) - rel_abs_dist
            pin_dist = np.sqrt(np.sum(np.square(abs_dist)))

            # Calculate a value that takes the GT box size
            # and absolute localization error into account
            dist_value = np.prod(rel_abs_dist_inv)

            matched_pin_dist[i] = pin_dist
            matched_dist_values[i] = dist_value

        mean_dist_value = 0.0
        if len(pin_gt_boxes) > 0:
            mean_dist_value = np.sum(matched_dist_values) / len(pin_gt_boxes)

        # Plausibility checks
        assert len(detected_pins) == (len(true_positives) +
                                      len(multiple_matches) + len(false_positives))
        assert len(pin_gt_boxes) == (len(true_positives) + len(not_matched_gt))

        return SimpleMetricResults(
            true_positive_matches=true_positives,
            false_positives=false_positives,
            false_negatives=not_matched_gt,
            multiple_matches=multiple_matches,
            tp_abs_distances=matched_pin_dist,
            tp_rbd=matched_dist_values,
            mean_tp_rbd=mean_dist_value
        )

    @classmethod
    def evaluate_dataset(cls, detector, chip_images, chip_image_margins, pin_gt_boxes,
                         chip_image_names=None, show_results=False):
        """
        Evaluate the chip detection metrics for a whole image data set

        :param detector:
        :param chip_images:
        :param chip_image_margins:
        :param pin_gt_boxes:
        :param chip_image_names:
        :param show_results:
        :return:
        """
        mean_rbd = 0.0
        num_false_detections = 0
        detection_time = 0.0
        acc_precision = 0.0
        acc_recall = 0.0

        for i, chip_image in enumerate(chip_images):
            gt_boxes = pin_gt_boxes[i]
            chip_image_margin = chip_image_margins[i]

            chip_image_name = i
            if chip_image_names is not None:
                chip_image_name = chip_image_names[i]

            cls.logger.debug("-------------------------------------")
            cls.logger.debug("Performing pin detection for image %s (%d/%d):",
                             chip_image_name, i + 1, len(chip_images))
            cls.logger.debug("-------------------------------------")

            t_start = time.time()
            detected_pins = detector.find_chip_pins(chip_image=chip_image,
                                                    chip_margin=chip_image_margin)
            t_end = time.time()
            detection_time += t_end - t_start

            # Calculate the metrics for the single image
            metrics = cls.calculate_simple_metric(pin_gt_boxes=gt_boxes,
                                                  detected_pins=detected_pins)

            mean_rbd += metrics.mean_tp_rbd
            num_false_detections += len(metrics.false_positives) + \
                len(metrics.multiple_matches)
            acc_precision += metrics.precision
            acc_recall += metrics.recall

            cls.logger.debug("True positives: %d",
                             len(metrics.true_positives))
            cls.logger.debug("Multi matches: %d",
                             len(metrics.multiple_matches))
            cls.logger.debug("Not matched GT: %d",
                             len(metrics.false_negatives))
            cls.logger.debug("Multi matches: %d",
                             len(metrics.multiple_matches))
            cls.logger.debug("False positives: %d",
                             len(metrics.false_positives))
            cls.logger.debug("RBD: %.3f", metrics.mean_tp_rbd)
            cls.logger.debug("Precision: %.3f", metrics.precision)
            cls.logger.debug("Recall: %.3f", metrics.recall)

            if show_results:
                res_image = chip_image.copy()
                res_image = draw_pin_detections(image=res_image,
                                                pins=cls._pin_ground_truth_boxes_to_pins(
                                                    gt_boxes),
                                                color=(0, 0, 0),
                                                fill_color=cls.COLOR_GROUND_TRUTH,
                                                draw_pin_contours=True)
                res_image = draw_pin_detections(image=res_image,
                                                pins=[p
                                                      for i, p in enumerate(detected_pins)
                                                      if i in metrics.true_positives],
                                                color=cls.COLOR_TRUE_POSITIVE)
                res_image = draw_pin_detections(image=res_image,
                                                pins=[p
                                                      for i, p in enumerate(detected_pins)
                                                      if i in metrics.false_positives],
                                                color=cls.COLOR_FALSE_POSITIVE)
                res_image = draw_pin_detections(image=res_image,
                                                pins=[p
                                                      for i, p in enumerate(detected_pins)
                                                      if i in metrics.multiple_matches],
                                                color=cls.COLOR_MUTLI_MATCH)

                cv2.imshow(f"Detection results ({chip_image_name})", res_image)

        # Calculate mean values
        mean_rbd /= len(chip_images)
        mean_false_positives = num_false_detections / len(chip_images)
        mean_detection_time = detection_time / len(chip_images)
        mean_precision = acc_precision / len(chip_images)
        mean_recall = acc_recall / len(chip_images)

        return DatasetEvalMetricResults(num_false_positives=num_false_detections,
                                        mean_false_positives=mean_false_positives,
                                        mean_rbd=mean_rbd,
                                        mean_detection_time=mean_detection_time,
                                        mean_precision=mean_precision,
                                        mean_recall=mean_recall)

    @staticmethod
    def _pin_ground_truth_boxes_to_pins(pin_gt_boxes):
        """
        Convert a list of pin ground truth boxes to
        pin results

        :param pin_gt_boxes: List of pin ground truth boxes
        :return A list of pin detections as returned by a
                PinDetector
        """
        gt_pins = []
        for pin_gt_box in pin_gt_boxes:
            pin_gt_center = np.array(((pin_gt_box[2] + pin_gt_box[0]) * 0.5,
                                      (pin_gt_box[3] + pin_gt_box[1]) * 0.5))
            pin_gt_contour = np.array([[pin_gt_box[0], pin_gt_box[1]],
                                       [pin_gt_box[0], pin_gt_box[3]],
                                       [pin_gt_box[2], pin_gt_box[3]],
                                       [pin_gt_box[2], pin_gt_box[1]]])
            gt_pins.append(Pin(center=pin_gt_center,
                               contour=[pin_gt_contour]))

        return gt_pins
