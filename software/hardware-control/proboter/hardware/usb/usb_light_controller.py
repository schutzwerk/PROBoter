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

from proboter.event_bus import EventBus
from proboter.hardware import LightController, LightControllerConfig

from .usb_axes_controller import UsbAxesController


class UsbLightController(LightController):
    """
    A simulated light controller which is always connected
    and only keeps track of the on / off value
    """

    def __init__(self, axes_controller: UsbAxesController,
                 event_bus: EventBus) -> None:
        LightController.__init__(self,
                                 LightControllerConfig(),
                                 event_bus)
        self._axes_controller = axes_controller

    async def start(self) -> None:
        """
        Set up and initialize the hardware unit
        """
        await self.sync()

    async def stop(self) -> None:
        """
        Shutdown the hardware unit
        """
        # Nothing to do here
        self.status.connected = False
        await self._status_changed()

    async def sync(self) -> None:
        """
        Force a synchronization with the state of the light controller hardware
        """
        self.status.connected = self._axes_controller.is_connected
        if self.status.connected:
            light_intensity = await self._axes_controller.get_light_intensity()
            self.status.on = light_intensity != self._axes_controller.MIN_LIGHT_INTENSITY
        else:
            self.status.on = False
        await self._status_changed()

    async def switch_on(self) -> None:
        """
        Turn the light on
        """
        await self._axes_controller.set_light_intensity(
            UsbAxesController.MAX_LIGHT_INTENSITY)
        self.status.on = True
        await self._status_changed()

    async def switch_off(self) -> None:
        """
        Turn the light off
        """
        await self._axes_controller.set_light_intensity(
            UsbAxesController.MIN_LIGHT_INTENSITY)
        self.status.on = False
        await self._status_changed()
