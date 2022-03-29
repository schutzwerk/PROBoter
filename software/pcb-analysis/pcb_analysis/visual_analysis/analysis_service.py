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

import uuid
import logging
from dataclasses import dataclass, field
from typing import Callable, Iterable, Optional

import numpy as np

from pcb_analysis.model import Pin, Chip
from pcb_analysis.pin_detection import PinDetector
from pcb_analysis.chip_detection import ChipDetector


@dataclass
class ChipDetectorDefinition:
    """
    Definition of chip detector containing meta data and
    a factory method to create a detector instance
    """
    # Unique identifier of the chip detector
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Name of the chip detector
    name: str = ""
    # Factory method to create a detector instance
    factory: Callable[[], ChipDetector] = None


@dataclass
class PinDetectorDefinition:
    """
    Definition of a pin detector containing meta data and
    a factory method to create a detector instance
    """
    # Unique identifier of the pin detector
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Name of the pin detector
    name: str = ""
    # Factory method to create a detector instance
    factory: Callable[[], ChipDetector] = None


@dataclass
class PcbImageAnalysisResult:
    """
    Results of the analyis of a single PCB image
    """
    # Iterable collection of identified chips / ICs
    chips: Iterable[Chip] = ()
    # Iterable collection of detected pins not belonging
    # to any chip like test pads
    pads: Iterable[Pin] = ()


class AnalysisService:
    """
    Service that provides operations to analyse PCB
    images for available chips, pins, etc.
    """

    log = logging.getLogger(__name__)

    def __init__(self):
        self._chip_detectors = []
        self._pin_detectors = []

        # Internally cached detector instances to
        # speed up subsequent detections
        self._chip_detector_instances = {}
        self._pin_detector_instances = {}

    @property
    def chip_detectors(self) -> Iterable[ChipDetectorDefinition]:
        """
        Return an iterable collection of registered chip detectors
        """
        return tuple(self._chip_detectors)

    @property
    def pin_detectors(self) -> Iterable[PinDetectorDefinition]:
        """
        Return an iterable collection of registered pin detectors
        """
        return tuple(self._pin_detectors)

    def get_chip_detector_by_id(self, chip_detecotr_id: str) -> Optional[ChipDetector]:
        """
        Return the chip detector with a given unique identifier

        :param chip_detecotr_id: Unique identifier of the chip detector
        :type chip_detecotr_id: str
        :return: A chip detector instance with the given identifier
        :rtype: Optional[ChipDetector]
        """
        detector = [d for d in self.chip_detectors
                    if d.id.lower() == chip_detecotr_id.lower()]

        # No suitable detector found
        if len(detector) < 1:
            return None

        # Return a new instance of the chip detector
        return detector[0]

    def get_pin_detector_by_id(self, pin_detector_id: str) -> Optional[PinDetector]:
        """
        Return the pin detector with a given unique identifier

        :param pin_detector_id: Unique identifier of the pin detector
        :type pin_detector_id: str
        :return: A pin detector instance with the given identifier
        :rtype: Optional[PinDetector]
        """
        detector = [d for d in self.pin_detectors
                    if d.id.lower() == pin_detector_id.lower()]

        # No suitable detector found
        if len(detector) < 1:
            return None

        # Return a new instance of the pin detector
        return detector[0]

    def add_chip_detector(self, name: str,
                          factory: Callable[[], ChipDetector],
                          chip_detector_id: str = str(uuid.uuid4())) -> None:
        """
        Register a new chip detector

        :param name: Displayable name of the chip detector
        :type name: str
        :param factory: Factory method to create a new detector instance
                        wich will be called for each analysis
        :type factory: Callable[[], ChipDetector]
        :param chip_detector_id: Unique identifier of the chip detector
        :type chip_detector_id: str
        """
        detector = ChipDetectorDefinition(name=name,
                                          factory=factory,
                                          id=chip_detector_id)
        self._chip_detectors.append(detector)

    def add_pin_detector(self, name: str,
                         factory: Callable[[], PinDetector],
                         pin_detector_id: str = str(uuid.uuid4())) -> None:
        """
        Register a new pin detector

        :param name: Displayable name of the pin detector
        :type name: str
        :param factory: Factory method to create a new detector instance
                        wich will be called for each analysis
        :type factory: Callable[[], PinDetector]
        :param pin_detector_id: Unique identifier of the pin detector
        :type pin_detector_id: str
        """
        detector = PinDetectorDefinition(name=name,
                                         factory=factory,
                                         id=pin_detector_id)
        self._pin_detectors.append(detector)

    def analyse_pcb_image(self, pcb_image: np.ndarray,
                          chip_detector_definition: ChipDetectorDefinition,
                          pin_detector_definition: Optional[PinDetectorDefinition]) \
            -> PcbImageAnalysisResult:
        """
        Analyze a PCB image with a given chip and pin detector

        :param pcb_image: PCB image to analyze
        :type pcb_image: np.ndarray
        :param chip_detector_definition: Chip detector that will be used to
                                         scan for chips / ICs
        :type chip_detector_definition: ChipDetectorDefinition
        :param pin_detector_definition: Pin detector that will be used to scan for pins
                                        in the proximity of the detected chips
        :type pin_detector_definition: PinDetectorDefinition
        :return: The located chips and corresponding pins
        :rtype: PcbImageAnalysisResult
        """

        # Instantiate the detectors
        self.log.info("Using chip detector: %s", chip_detector_definition.name)
        if not chip_detector_definition.id in self._chip_detector_instances:
            detector = chip_detector_definition.factory()
            self._chip_detector_instances[chip_detector_definition.id] = detector
        chip_detector = self._chip_detector_instances[chip_detector_definition.id]

        # Perform chip detection
        self.log.info("Searching for chips...")
        chip_detections = chip_detector.detect_chips(pcb_image)
        self.log.info("Found %d chips", len(chip_detections))

        if pin_detector_definition is None:
            self.log.info("Skipping pin detection")
        else:
            # Fetch the requested pin detector instance
            self.log.info("Using pin detector: %s",
                          pin_detector_definition.name)
            if not pin_detector_definition.id in self._pin_detector_instances:
                detector = pin_detector_definition.factory()
                self._pin_detector_instances[pin_detector_definition.id] = detector
            pin_detector = self._pin_detector_instances[pin_detector_definition.id]

            # Extract the chip images
            self.log.info("Extracting chip images...")
            chip_images, chip_offsets = PinDetector.extract_chips(board_image=pcb_image,
                                                                  chip_detections=chip_detections)

            # Perform pin detection
            for i, chip_img in enumerate(chip_images):
                self.log.info('Searching pins for chip %d of %d',
                              i + 1, len(chip_images))
                pin_detections = pin_detector.find_chip_pins(chip_image=chip_img,
                                                             chip_margin=30)

                # Calculate the absolute image coordinates of the detected pins
                for pin_detection in pin_detections:
                    img_center = pin_detection.center + chip_offsets[i, :]
                    pin_detection.center = img_center.reshape((-1,))
                    pin_detection.contour = pin_detection.contour.reshape(
                        (-1, 2))

                chip_detections[i].pins = pin_detections
                self.log.info('%d pins found for chip %d',
                              len(pin_detections), i + 1)

        return PcbImageAnalysisResult(chips=chip_detections)

    def release(self) -> None:
        """
        Free all allocated resources
        """
        self.log.info("Releasing chip detectors")
        for detector in self._chip_detector_instances.values():
            detector.release()
        self._chip_detector_instances = {}

        self.log.info("Releasing pin detectors")
        for detector in self._pin_detector_instances.values():
            detector.release()
        self._pin_detector_instances = {}
