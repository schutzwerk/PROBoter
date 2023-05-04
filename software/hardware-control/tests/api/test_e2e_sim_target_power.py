# Copyright (C) 2023 SCHUTZWERK GmbH
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

import pytest
from quart import Quart

from proboter import create_app


@pytest.mark.asyncio
async def test_default_simulation_target_power_status(app):
    test_client = app.test_client()
    response = await test_client.get("/api/v1/power-controller")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": False}


@pytest.mark.asyncio
async def test_switch_target_power_on(app):
    test_client = app.test_client()
    response = await test_client.get("/api/v1/power-controller")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": False}

    response = await test_client.post("/api/v1/power-controller/on")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": True}


@pytest.mark.asyncio
async def test_switch_target_power_off(app):
    test_client = app.test_client()
    response = await test_client.get("/api/v1/power-controller")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": False}

    response = await test_client.post("/api/v1/power-controller/on")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": True}

    response = await test_client.post("/api/v1/power-controller/off")
    assert response.status_code == 200
    response_data = await response.json
    assert response_data == {"connected": True,
                             "on": False}
