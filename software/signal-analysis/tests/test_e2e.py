# Copyright (C) 2022  SCHUTZWERK GmbH
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

import json
from pathlib import Path
from datetime import datetime

from schema import Schema, Or


def test_e2e_analyse_i2c_json_data(client, data_i2c):
    """
    E2E test of the voltage signal measurement analysis resource
    parsing JSON data
    """
    data = [{'index': 0,
             'source_name': 'Picoscope',
             'voltage_levels': channel.data,
             'measurement_resolution': data_i2c.resolution,
             'start_time': datetime.now()
             } for channel in data_i2c.channels]

    response = client.post("/api/v1/analysis",
                           json=data)

    schema = Schema([{
        "protocolName": str,
        "signals": {
            "clock": Or(int, None),
            "data1": Or(int, None),
            "data2": Or(int, None),
            "control": Or(int, None)
        },
        "identificationRatings": {
            "I2C": float,
            "SPI": float,
            "UART": float,
            "OneWire": float
        },
        "encodingParameters": dict,
        "correlationRating": Or(float, None)
    }])
    assert schema.validate(response.json)
    assert len(response.json) > 0


def test_e2e_analysis_i2c_csv_file(client, data_i2c_path):
    """
    E2E test of the voltage signal measurement analysis resource
    parsing CSV file(s)
    """
    response = client.post("/api/v1/analysis/file",
                           data={
                               "voltage-datasets": data_i2c_path.open('rb'),
                           })

    schema = Schema([{
        "protocolName": str,
        "signals": {
            "clock": Or(int, None),
            "data1": Or(int, None),
            "data2": Or(int, None),
            "control": Or(int, None)
        },
        "identificationRatings": {
            "I2C": float,
            "SPI": float,
            "UART": float,
            "OneWire": float
        },
        "encodingParameters": dict,
        "correlationRating": Or(float, None)
    }])
    assert schema.validate(response.json)
    assert len(response.json) > 0


def test_e2e_analysis_test_against_reference_results(client, resources_path: Path):
    """
    E2E test of the voltage signal measurement analysis resource
    parsing CSV file(s)
    """
    # Load the reference values
    reference_value_file = resources_path / 'reference_detections.json'
    with reference_value_file.open('r', encoding='utf-8') as f:
        reference_data = json.loads(f.read())

    for i, reference_result in enumerate(reference_data):
        csv_file = resources_path / reference_result['filename']
        analysis_results = reference_result['results']

        response = client.post("/api/v1/analysis/file",
                               data={
                                   "voltage-datasets": csv_file.open('rb'),
                               })
        assert response.json == analysis_results, \
            f'Results for file {csv_file} ({i + 1} / {len(reference_data)}) differ'
