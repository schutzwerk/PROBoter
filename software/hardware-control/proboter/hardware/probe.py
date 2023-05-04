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
from abc import abstractmethod

import numpy as np

from proboter.event_bus import EventBus
from proboter.model import ProbeType, ProbeConfig

from .axis_direction import AxisDirection
from .hardware_unit import HardwareUnit
from .events import ProbeStatus, ProbeStatusChangedEvent


class Probe(HardwareUnit[ProbeConfig, ProbeStatus]):
    """
    Base class for a high-level control of a probe unit
    """

    log = logging.getLogger(__module__)

    def __init__(self, config: ProbeConfig, event_bus: EventBus) -> None:
        """
        Initialize a probe

        :param config: _description_
        :type config: ProbeConfig
        :param event_bus: _description_
        :type event_bus: EventBus
        """
        HardwareUnit.__init__(self, config, ProbeStatus(id=config.id,
                                                        name=config.name,
                                                        order_index=config.order_index,
                                                        probe_type=config.probe_type,
                                                        connected=False))

        # Event bus to emit state change events to
        self._event_bus = event_bus

    @property
    def is_connected(self) -> bool:
        """
        Whether the probe is connected

        :rtype: bool
        """
        return self.status.connected

    @property
    def id(self) -> int:
        """
        Return the unique probe identifier
        """
        return self.config.id

    @property
    def name(self) -> str:
        """
        Return the symbolic name of the probe
        """
        return self.config.name

    @property
    def order_index(self) -> int:
        """
        Return the numerical order index of the probe
        used for collision detection and path planning
        """
        return self.config.order_index

    @property
    def probe_type(self) -> ProbeType:
        """
        Return the probe type that defines the location
        of the probe in the PROBoter hardware platform
        """
        return self.config.probe_type

    @property
    def tmat_local_to_global(self) -> np.ndarray:
        """
        Return the (4x4) transformation matrix that defines the
        transformation from the probe local to the global
        coordinate system
        """
        return self.config.tmat_to_glob

    @property
    def position(self) -> np.ndarray:
        """
        Return the probe's current position in local coordinates
        as numpy (1x3) array
        """
        return self.status.current_position_local

    @property
    def position_global(self) -> np.ndarray:
        """
        Return the probe's current position in global coordinates
        as numpy (1x3) array
        """
        return self.status.current_position_global

    @property
    def positive_x_safety_position(self) -> np.ndarray:
        """
        Return the safety position on the left part
        of the proboter (positive x values) in probe-local
        coordinates.
        """
        return self.config.pos_x_safety_position

    @property
    def negative_x_safety_position(self) -> np.ndarray:
        """
        Return the safety position on the right part
        of the proboter (negative x values) in probe-local
        coordinates.
        """
        return self.config.neg_x_safety_position

    @property
    def safety_position(self) -> np.ndarray:
        """
        Return the primary safety position of this probe.
        The primary safety position is the safety position
        nearest to the homed position of the probe.

        For probes 2.1 and 2 this is pos_x_safety_position
        For probes 1.1 and 1 this is neg_x_safety_position
        """
        if self.config.probe_type in [ProbeType.P2, ProbeType.P21]:
            return self.positive_x_safety_position

        return self.negative_x_safety_position

    def map_local_to_global_point(self, local_point: np.ndarray) -> np.ndarray:
        """
        Transform a single 3D point from the local probe coordinate system
        to the global system

        :param local_point: Point in the local probe system as (1x3) numpy array
        :type local_point: numpy.ndarray
        :return: The corresponding point in the global coordinate system
                 as (1x3) numpy array
        :rtype: numpy.ndarray
        """
        local_point = np.reshape(local_point, (-1, 3))
        global_point = self.map_local_to_global_points(local_point)
        global_point = np.reshape(global_point, 3)
        return global_point

    def map_local_to_global_points(
            self, local_points: np.ndarray) -> np.ndarray:
        """
        Transform points from the probe local to the global coordinate system

        :param local_points: n points in the local probe coordinate system
                             as (nx3) numpy array
        :type local_points: numpy.ndarray
        :return: The corresponding points in the global coordinate system
                 as (nx3) numpy array
        :rtype: numpy.ndarray
        """
        # Extend the points to 3D homogeneous coordinates
        points = np.ones((local_points.shape[0], 4))
        points[:, 0:3] = local_points
        global_points = np.matmul(
            self.tmat_local_to_global, points.T).T[:, 0:3]

        return global_points

    def map_global_to_local_point(self, global_point: np.ndarray):
        """
        Transform a single 3D point from the global coordinate system
        to the local probe system

        :param global_point: Point in the local probe system as (1x3) numpy array
        :type global_point: numpy.ndarray
        :return: The corresponding point in the global coordinate system
                 as (1x3) numpy array
        :rtype: numpy.ndarray
        """
        global_point = np.reshape(global_point, (-1, 3))
        local_point = self.map_global_to_local_points(global_point)
        local_point = np.reshape(local_point, 3)
        return local_point

    def map_global_to_local_points(
            self, global_points: np.ndarray) -> np.ndarray:
        """
        Transform points from the local probe to the global coordinate system

        :param global_points: The points in the global coordinate system to
                           transform as (nx3) numpy array
        :type global_points: np.ndarray
        :return: The corresponding points in the local probe system
                 as (nx3) numpy array
        :rtype: np.ndarray
        """

        # Extend the points to 3D homogeneous coordinates
        points = np.ones((global_points.shape[0], 4))
        points[:, 0:3] = global_points
        inverse = np.linalg.inv(self.tmat_local_to_global)
        local_points = np.matmul(inverse, points.T).T[:, 0:3]
        return local_points

    @abstractmethod
    async def home(self, axis: Optional[AxisDirection] = None) -> None:
        """
        Home the probe by moving to it's endstops

        :param axis: Optional single axis to home. If None, all axes are homed.
        :type axis: Optional[AxisDirection]
        """

    @abstractmethod
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

    @abstractmethod
    async def move_to_local_position(self, position: np.ndarray,
                                     feed: float = 300) -> None:
        """
        Hardware-specific implementation to move a probe to a new position in
        the probe's local coordinate system

        :param position: New probe position in the probe's local coordinate
                         system
        :type position: np.ndarray
        :param feed: Movement feed in mm/min, defaults to 300
        :type feed: float, optional
        """

    async def move_to_global_position(self, position: np.ndarray,
                                      feed: float = 300, raise_z: bool = False) -> None:
        """
        Move the unit to a given absolute position in the probe's local system

        This methods blocks until the target position is reached

        :param position: A numpy (1x3) array of the (x, y, z) coordinates in mm
        :type position: np.ndarray
        :param feed: The feed rate for all axes in mm/min
        :param raise_z: Boolean value which determines whether the probe is
                        raised in z before moving
        :type raise_z: bool
        """
        if raise_z:
            # Raise the Z axis first
            tmp_pos = self.position.copy()
            tmp_pos[2] = 0
            await self.move_to_local_position(tmp_pos, feed)

        local_position = self.map_global_to_local_point(position)

        # Move to the target location
        await self.move_to_local_position(local_position, feed)

    async def move_to_pos_x_safety_position(self) -> None:
        """
        Move the probe to it's positive x safety position
        """
        self.log.debug("Moving probe %s to it's positive x  safety position",
                       self.name)
        await self.move_to_local_position(self.positive_x_safety_position)

    async def move_to_neg_x_safety_position(self) -> None:
        """
        Move the probe to it's negative x safety position
        """
        self.log.debug("Moving probe %s to it's negative x safety position",
                       self.name)
        await self.move_to_local_position(self.negative_x_safety_position)

    async def move_to_safety_position(self) -> None:
        """
        Move the probe to it's safety position
        """
        self.log.debug("Moving probe %s to it's safety position", self.name)
        await self.move_to_local_position(self.safety_position)

    def _update_local_position(self, position: np.ndarray) -> None:
        """
        Update the probe's current position in the local coordinate system

        The position in the global coordinate system is automatically updated

        :param position: New probe position
        :type position: np.ndarray
        """
        self.status.current_position_local = position.copy()
        self.status.current_position_global = self.map_local_to_global_point(
            self.status.current_position_local)

    async def _status_changed(self) -> None:
        """
        Event handler for controller state changed events
        """
        event = ProbeStatusChangedEvent(id=self.config.id,
                                        status=self.status)
        await self._event_bus.emit_event(event)
