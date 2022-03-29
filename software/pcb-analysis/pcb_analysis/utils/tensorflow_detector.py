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
from typing import Dict, Any

import numpy as np
import tensorflow as tf


class TensorflowDetector:
    """
    An object detector using models from the
    Tensorflow Object Detection API

    https://github.com/tensorflow/models/tree/master/research/object_detection
    """

    logger = logging.getLogger(__module__)

    def __init__(self, model_file='', conf_threshold=0.0):
        self.model_file = model_file
        self.conf_threshold = conf_threshold

        self.detection_graph = None
        self.session = None
        self.tensor_dict = None
        self.image_tensor = None

    def _init(self):
        if self.session is None:
            # Read the trained model (graph and weights)
            self.detection_graph = tf.Graph()
            # pylint: disable=locally-disabled, not-context-manager
            # This is the recommended way for lazy execution, see
            # https://www.tensorflow.org/api_docs/python/tf/Graph
            with self.detection_graph.as_default():
                od_graph_def = tf.compat.v1.GraphDef()
                with tf.io.gfile.GFile(self.model_file, 'rb') as fid:
                    serialized_graph = fid.read()
                    od_graph_def.ParseFromString(serialized_graph)
                    tf.import_graph_def(od_graph_def, name='')

            # Create a Tensorflow session
            self.session = tf.compat.v1.Session(graph=self.detection_graph)

            # Get handles to input and output tensors
            ops = self.detection_graph.get_operations()
            all_tensor_names = {
                output.name for op in ops for output in op.outputs}
            self.tensor_dict = {}
            for key in [
                'num_detections', 'detection_boxes', 'detection_scores',
                'detection_classes', 'detection_masks'
            ]:
                tensor_name = key + ':0'
                if tensor_name in all_tensor_names:
                    self.tensor_dict[key] = self.detection_graph.get_tensor_by_name(
                        tensor_name)
            self.image_tensor = self.detection_graph.get_tensor_by_name(
                'image_tensor:0')

    def detect(self, image: np.ndarray, label_dict: Dict[int, str]) -> Dict[str, Any]:
        """
        Perform object detection with the defined Tensorflow model

        :param image: Image to analyse
        :type image: np.ndarray
        :param label_dict: Dictionary that maps numerical class labels to
                           human-readable strings
        :type label_dict: Dict[int, str]
        :retrun: Dictionary with identified object instances
        :rtype: Dict[str, Any]
        """
        # Actual detection.
        output_dict = self._run_inference_for_single_image(image)

        # Convert results to numpy arrays
        scores = np.array(output_dict['detection_scores'])
        boxes = np.array(output_dict['detection_boxes'])
        classes = np.array(output_dict['detection_classes'])

        # Thresholding
        idx = np.nonzero(scores >= self.conf_threshold)
        valid_scores = scores[idx]
        valid_classes = classes[idx]
        valid_boxes = np.take(boxes, idx, axis=0)[0]

        self.logger.debug("Scores: %s", valid_scores.tolist())
        self.logger.debug("Classes: %s", valid_classes.tolist())
        self.logger.debug("Boxes: %s", valid_boxes.tolist())

        return self._convert_detections(classes=valid_classes,
                                        scores=valid_scores,
                                        boxes=valid_boxes,
                                        image=image,
                                        label_dict=label_dict)

    def _run_inference_for_single_image(self, image: np.ndarray) -> Dict[str, Any]:
        # Setup
        self._init()

        # Run inference
        start_time = time.time()
        output_dict = self.session.run(self.tensor_dict,
                                       feed_dict={self.image_tensor: np.expand_dims(image, 0)})
        end_time = time.time()
        self.logger.info("Inference took %.3f seconds", end_time - start_time)

        # all outputs are float32 numpy arrays, so convert types as appropriate
        output_dict['num_detections'] = int(output_dict['num_detections'][0])
        output_dict['detection_classes'] = output_dict[
            'detection_classes'][0].astype(np.uint8)
        output_dict['detection_boxes'] = output_dict['detection_boxes'][0]
        output_dict['detection_scores'] = output_dict['detection_scores'][0]

        return output_dict

    @staticmethod
    def _convert_detections(classes, scores, boxes, image, label_dict):
        img_height, img_width, _ = image.shape
        converted_detections = []
        for idx, score in enumerate(scores):
            box = boxes[idx]
            label = label_dict[classes[idx]]
            # Bounding boxes encoding:
            # box[0] = y_min
            # box[1] = x_min
            # box[2] = y_max
            # box[3] = x_max
            x_min = box[1]
            y_min = box[0]
            x_max = box[3]
            y_max = box[2]

            obj_img = image[int(y_min * img_height):int(y_max * img_height),
                            int(x_min * img_width):int(x_max * img_width), :]

            converted_detections.append(
                {'type': label,
                 'conf': float(score),
                 'image': obj_img,
                 'bbox': np.array([[x_min * img_width, y_min * img_height],
                                   [x_max * img_width, y_min * img_height],
                                   [x_max * img_width, y_max * img_height],
                                   [x_min * img_width, y_max * img_height]], float)
                 })

        return converted_detections

    def release(self) -> None:
        """
        Free allocated resources from Tensorflow session
        """
        if self.session is not None:
            # Close session to free resources
            self.session.close()
