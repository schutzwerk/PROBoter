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

from pathlib import Path

import cv2
import pytest

from pcb_analysis import create_app

# Get the resources folder in the tests folder
resources = Path(__file__).parent / "resources"


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
def pcb_image_path():
    return resources / "sample_pcb.png"


@pytest.fixture()
def pcb_image(pcb_image_path):
    return cv2.imread(str(pcb_image_path))


@pytest.fixture()
def ic_image():
    return cv2.imread(str(resources / "sample_ic.png"))


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()
