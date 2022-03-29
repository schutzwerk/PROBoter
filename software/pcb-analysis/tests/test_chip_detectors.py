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

from pcb_analysis.chip_detection import ColorBasedChipDetector, \
    TensorflowChipDetector


def test_color_based_chip_detector_detect_with_valid_image(pcb_image):
    """
    Test the chip detection functionality of the ColorBasedChipDetector
    """
    detector = ColorBasedChipDetector()
    result = detector.detect_chips(pcb_image)

    assert result is not None


def test_tensorflow_chip_detector_with_valid_image(pcb_image):
    """
    Test the chip detection functionality of the TensorflowChipDetector
    """
    detector = TensorflowChipDetector()
    result = detector.detect_chips(pcb_image)

    assert result is not None
