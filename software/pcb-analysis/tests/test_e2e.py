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

import os
import tempfile

from schema import Schema, Or


def test_e2e_list_chip_detectors(client):
    """
    E2E test of the chip detector GET resource
    """
    schema = Schema([{"id": str,
                      "name": str}])
    response = client.get("/api/v1/detectors/chip")
    assert schema.validate(response.json)
    assert len(response.json) > 0


def test_e2e_list_pin_detectors(client):
    """
    E2E test of the pin detector GET resource
    """
    schema = Schema([{"id": str,
                      "name": str}])
    response = client.get("/api/v1/detectors/pin")
    assert schema.validate(response.json)
    assert len(response.json) > 0


def test_e2e_analysis_fail_with_inalid_pcb_image(client):
    """
    E2E test of the PCB image analysis POST resource
    with an invalid PCB image
    """
    # Hard-coded "Faster R-CNN" chip detector
    chip_detector = "ded48437-36bc-4116-a374-1aaa6b0d7681"
    # Hard-coded "CV pipeline" pin detector
    pin_detector = "8956bee0-ee4e-497b-a471-97aa8724e6b4"

    with tempfile.NamedTemporaryFile(suffix=".png") as tmp_file:
        tmp_file.write(os.urandom(1024))
        response = client.post("/api/v1/analysis",
                               data={
                                   "pcb-image": tmp_file,
                                   "chip-detector": chip_detector,
                                   "pin-detector": pin_detector
                               })
    assert response.status_code == 400
    assert {"message": "Invalid or malformed PCB image"} == response.json


def test_e2e_analysis_fail_with_invalid_chip_detector(client, pcb_image_path):
    """
    E2E test of the PCB image analysis POST resource
    with an invalid chip detector ID
    """
    chip_detector = "11111111-1111-1111-1111-11111111"

    response = client.post("/api/v1/analysis",
                           data={
                               "pcb-image": pcb_image_path.open("rb"),
                               "chip-detector": chip_detector
                           })
    assert response.status_code == 400
    assert {"message": "Unknown chip detector"} == response.json


def test_e2e_analysis_fail_with_invalid_pin_detector(client, pcb_image_path):
    """
    E2E test of the PCB image analysis POST resource
    with an invalid pin detector ID
    """
    # Hard-coded "Faster R-CNN" chip detector
    chip_detector = "ded48437-36bc-4116-a374-1aaa6b0d7681"
    pin_detector = "11111111-1111-1111-1111-11111111"

    response = client.post("/api/v1/analysis",
                           data={
                               "pcb-image": pcb_image_path.open("rb"),
                               "chip-detector": chip_detector,
                               "pin-detector": pin_detector
                           })
    assert response.status_code == 400
    assert {"message": "Unknown pin detector"} == response.json


def test_e2e_analysis_with_json_response(client, pcb_image_path):
    """
    E2E test of the PCB image analysis POST resource
    """
    # Hard-coded "Faster R-CNN" chip detector
    chip_detector = "ded48437-36bc-4116-a374-1aaa6b0d7681"
    # Hard-coded "CV pipeline" pin detector
    pin_detector = "8956bee0-ee4e-497b-a471-97aa8724e6b4"

    schema = Schema({
        "components": [{
            "id": str,
            "package": str,
            "confidence": float,
            "vendor": Or(str, None),
            "marking": Or(str, None),
            "contour": [[float, float]],
            "pins": [{
                "id": str,
                "confidence": float,
                "center": [float]
            }]
        }],
        "pads": [{
            "id": str,
            "confidence": float,
            "center": [float]
        }]})

    response = client.post("/api/v1/analysis",
                           data={
                               "pcb-image": pcb_image_path.open("rb"),
                               "chip-detector": chip_detector,
                               "pin-detector": pin_detector
                           })
    assert response.status_code == 200, response.json
    assert schema.validate(response.json)


def test_e2e_analysis_with_image_response(client, pcb_image_path):
    """
    E2E test of the PCB image analysis POST resource
    """
    # Hard-coded "Faster R-CNN" chip detector
    chip_detector = "ded48437-36bc-4116-a374-1aaa6b0d7681"
    # Hard-coded "CV pipeline" pin detector
    pin_detector = "8956bee0-ee4e-497b-a471-97aa8724e6b4"

    response = client.post("/api/v1/analysis",
                           headers={
                               "Accept": "image/png"
                           },
                           data={
                               "pcb-image": pcb_image_path.open("rb"),
                               "chip-detector": chip_detector,
                               "pin-detector": pin_detector
                           })
    assert response.status_code == 200, response.json
