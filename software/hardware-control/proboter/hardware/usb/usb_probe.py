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
from typing import Optional

import numpy as np

from proboter.event_bus import EventBus
from proboter.model import ProbeConfig
from proboter.hardware import Probe, ProbeMoveStartEvent, ProbeMoveFinishEvent, AxisDirection

from .usb_axes_controller import UsbAxesController


class UsbProbe(Probe):
    """
    High-level control of a probe unit
    """

    log = logging.getLogger(__module__)

    def __init__(self, probe_config: ProbeConfig, event_bus: EventBus,
                 axes_controller: UsbAxesController):
        """
        Initialize a new USB probe

        :param probe_config: Probe configuration
        :type probe_config: ProbeConfig
        :param event_bus: Event bus where probe-related events will be published
        :type event_bus: EventBus
        :param axes_controller: Underlying axes controller that moves the probe
        :type axes_controller: UsbAxesController
        """
        Probe.__init__(self, probe_config, event_bus)
        self._axes_controller = axes_controller

    async def start(self) -> None:
        """
        Start up the probe unit

        This basically initializes the underlying axes controller unit
        """
        if self._axes_controller is not None:
            await self._axes_controller.start()
        # Initial synchronization with the hardware
        await self.sync()

    async def stop(self) -> None:
        """
        Shutdown the probe unit

        The connection the underlying axes controller unit is closed
        and all acquired resources are released.
        """
        if self._axes_controller is not None:
            await self._axes_controller.stop()
        await self.sync()

    async def sync(self) -> None:
        """
        Force synchronization with the hardware's state
        """
        # Sync the connection state with the underlying axes controller
        self.status.connected = self._axes_controller.is_connected
        # If connected also read the current probe position
        if self.status.connected:
            self.status.current_position_local = await self._axes_controller.get_position()
        # Always calculate the global position based on the local one
        self._update_local_position(self.status.current_position_local)
        # Emit a status update event
        await self._status_changed()

    async def home(self, axis: Optional[AxisDirection] = None) -> None:
        """
        Home the probe by moving to it's endstops

        :param axis: Optional single axis to home. If None, all axes are homed.
        :type axis: Optional[AxisDirection]
        """
        self.log.debug("Homing probe %s", self.name)
        self.status.moving = True
        await self._status_changed()
        if axis is not None:
            await self._axes_controller.home([axis,])
        else:
            await self._axes_controller.home()
        self.status.moving = False
        await self.sync()

    async def center_probe(self) -> np.ndarray:
        """
        Runs a 4-point incremental probe centering cycle.
        Before running this, the probe must be positioned so
        that it touches the reference pin when lowering the
        z axis. If not, the probe can be damaged or destroyed!!

        :return: A numpy array of dimensions (4x3) with the
                 coordinates of the reference pin edge
        :rtype: np.ndarray
        """
        self.log.debug("Centering probe %s", self.name)
        self.status.moving = True
        await self._status_changed()
        ref_pins = await self._axes_controller.center_probe()
        self.status.moving = False
        await self.sync()
        return ref_pins

    async def move_to_local_position(self, position: np.ndarray,
                                     feed: float = 300) -> None:
        """
        Hardware-specific implementation to move a probe to a new position

        :param position: New probe position in the probe's local coordinate
                         system
        :type position: np.ndarray
        :param feed: Movement feed in mm/min, defaults to 300
        :type feed: float, optional
        """
        self.log.debug("Moving probe %s to position %s",
                       self.probe_type.value, position)
        self.status.moving = True
        await self._status_changed()

        start_event = ProbeMoveStartEvent(probe_type=self.probe_type,
                                          start_local=self.position,
                                          start_global=self.map_local_to_global_point(
                                              self.position),
                                          destination_local=position,
                                          destination_global=self.map_local_to_global_point(
                                              position),
                                          feed=feed)
        await self._event_bus.emit_event(start_event)
        await self._axes_controller.move_to_position(position, feed)
        await self._event_bus.emit_event(ProbeMoveFinishEvent(probe_type=self.probe_type))
        self.status.moving = False
        await self.sync()
