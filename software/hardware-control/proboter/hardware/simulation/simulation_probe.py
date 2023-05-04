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

import asyncio
import logging
from typing import Optional

import numpy as np

from proboter.event_bus import EventBus
from proboter.model import ProbeConfig
from proboter.hardware import Probe, ProbeMoveStartEvent, ProbeMoveFinishEvent, AxisDirection


class SimulationProbe(Probe):
    """
    Simulation of a PROBoter probing unit
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: ProbeConfig, event_bus: EventBus):
        Probe.__init__(self, config, event_bus)
        # The simulated probe position in the local coordinate system

    async def start(self) -> None:
        """
        Start up the probe unit

        This basically initializes the underlying axes controller unit
        """
        self.status.connected = True
        self._update_local_position(self.safety_position)
        await self._status_changed()

    async def stop(self) -> None:
        """
        Shutdown the probe unit

        The connection the underlying axes controller unit is closed
        and all acquired resources are released.
        """
        self.status.connected = False
        self._update_local_position(self.safety_position)
        await self._status_changed()

    async def home(self, axis: Optional[AxisDirection] = None) -> None:
        """
        Home the probe by moving to it's endstops

        :param axis: Optional single axis to home. If None, all axes are homed.
        :type axis: Optional[AxisDirection]
        """
        self.log.debug("Homing simulation probe %s", self.name)
        self.status.moving = True
        await self._status_changed()

        await asyncio.sleep(1.5)

        # Set the position after homing
        self.status.moving = False
        self._update_local_position(self.safety_position)
        await self._status_changed()

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
        raise NotImplementedError()

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

        # Calculate the movement time
        dist = position - self.position
        dist = np.sqrt(np.sum(np.square(dist)))
        movement_time_seconds = (dist / feed) * 60
        await asyncio.sleep(movement_time_seconds)

        await self._event_bus.emit_event(ProbeMoveFinishEvent(probe_type=self.probe_type))

        # Update the current position
        self.status.moving = False
        self._update_local_position(position)
        await self._status_changed()
