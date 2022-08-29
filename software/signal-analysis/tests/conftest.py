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

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Iterable

import pytest

from signal_analysis import create_app

# Get the resources folder in the tests folder
resources = Path(__file__).parent / "resources"


@dataclass
class CsvChannel:
    """
    CSV file measurement data of a single channel
    """
    name: str
    data: List[float] = field(default_factory=list)


@dataclass
class CsvData:
    """
    CSV file measurement data
    """
    filename: str = ''
    resolution: float = 0.0
    channels: Iterable[CsvChannel] = None


def read_csv_data(filename: Path, separator: str = ',') -> CsvData:
    """
    Simple CSV measurement data parser

    :param filename: CSV file to parse
    :type filename: Path
    :param separator: CSV value separator, defaults to ','
    :type separator: str, optional
    :return: Parsed CSV measurement data
    :rtype: CsvData
    """
    # Read the CSV file
    csv = CsvData(filename=filename.name)
    with open(filename, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.read().strip().split('\n')]

    # Resolution is the first line
    csv.resolution = int(lines[0].split(separator)[0])

    # Parse the channel names
    csv.channels = [CsvChannel(name=val.strip())
                    for val in lines[1].split(separator)]

    # Parse the data
    for data_line in lines[2:]:
        for i, val in enumerate(data_line.split(separator)):
            csv.channels[i].data.append(float(val))

    return csv


@pytest.fixture()
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def resources_path():
    return resources


@pytest.fixture()
def data_i2c_path(resources_path):
    return resources_path / "i2c.csv"


@pytest.fixture()
def data_i2c(data_i2c_path):
    return read_csv_data(data_i2c_path)
