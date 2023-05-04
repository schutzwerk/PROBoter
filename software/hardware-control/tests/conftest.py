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

import pytest_asyncio
from quart import Quart

from proboter import create_app


@pytest_asyncio.fixture(name="app", scope="function")
async def _app() -> Quart:
    app = create_app({
        "TESTING": True,
        "HARDWARE_BACKEND": "simulation"
    })

    async with app.test_app() as test_app:
        yield test_app
