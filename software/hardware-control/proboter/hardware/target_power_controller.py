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

from abc import abstractmethod

from proboter.model import TargetPowerControllerConfig
from proboter.event_bus import EventBus

from .hardware_unit import HardwareUnit
from .events import TargetPowerControllerStatus, TargetPowerControllerChangedEvent


class TargetPowerController(HardwareUnit[TargetPowerControllerConfig,
                                         TargetPowerControllerStatus]):
    """
    Interface of an abstract target power controller
    """

    def __init__(self, config: TargetPowerControllerConfig,
                 event_bus: EventBus) -> None:
        HardwareUnit.__init__(self, config, TargetPowerControllerStatus())
        # Event bus to emit state change events to
        self._event_bus = event_bus

    @abstractmethod
    async def switch_power_on(self) -> None:
        """
        Turn the power on
        """

    @abstractmethod
    async def switch_power_off(self) -> None:
        """
        Turn the power off
        """

    async def _status_changed(self) -> None:
        """
        Send a notification about status changes on the event bus
        """
        event = TargetPowerControllerChangedEvent(status=self.status)
        await self._event_bus.emit_event(event)
