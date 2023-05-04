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

import logging

from proboter.event_bus import EventBus
from proboter.model import TargetPowerControllerConfig
from proboter.hardware import TargetPowerController


class SimulationTargetPowerController(TargetPowerController):
    """
    Simulation of a target power controller
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: TargetPowerControllerConfig,
                 event_bus: EventBus) -> None:
        TargetPowerController.__init__(self, config, event_bus)

    async def start(self) -> None:
        """
        Set up and initialize the hardware unit
        """
        self.status.connected = True
        await self._status_changed()

    async def stop(self) -> None:
        """
        Shutdown the hardware unit
        """
        self.status.connected = False
        await self._status_changed()

    async def switch_power_on(self) -> None:
        """
        Turn the power on
        """
        self.log.info("Switching target power on")
        self.status.on = True
        await self._status_changed()

    async def switch_power_off(self) -> None:
        """
        Turn the power off
        """
        self.log.info("Switching target power off")
        self.status.on = False
        await self._status_changed()
