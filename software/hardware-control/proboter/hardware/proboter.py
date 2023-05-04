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
from typing import Iterable, Optional, Dict, Sequence

import numpy as np

from proboter.model import ProboterConfig, ProbeType

from .move_coordinator import MoveCoordinator, InvalidDestinationsError
from .target_power_controller import TargetPowerController

from .events import ProboterStatus
from .probe import Probe
from .camera import Camera
from .static_camera import StaticCamera
from .movable_camera import MovableCamera
from .light_controller import LightController
from .signal_multiplexer import SignalMultiplexer
from .picoscope import Picoscope
from .uart_interface_adapter import UartInterfaceAdapter
from .axis_direction import AxisDirection


class Proboter:
    """
    A class that provides high-level access to the
    PROBoter hardware.

    It also provides additional features like camera to
    probe mapping.
    """
    log = logging.getLogger(__module__)

    def __init__(self, config: ProboterConfig = None,
                 static_cameras: Iterable[StaticCamera] = (),
                 movable_cameras: Iterable[MovableCamera] = (),
                 probes: Iterable[Probe] = (),
                 light_controller: LightController = None,
                 target_power_controller: TargetPowerController = None,
                 signal_multiplexer: SignalMultiplexer = None,
                 picoscope: Picoscope = None,
                 uart_interface_adapter: UartInterfaceAdapter = None):
        """
        Initialize a PROBoter with cameras and probes

        :param config: The PROBoter configuration
        :param static_cameras: The PROBoter's static camera systems
        :param movable_cameras: The PROBoter's movable camera systems
        :param probes: The PROBoter probes
        :param light_controller: The PROBoter light controller
        :param power_switch_controller: The PROBoter power switch controller
        :param signal_multiplexer: The signal multiplexer used to
                                   route the probe signals
        :param uart_adapter: The UART / serial target adapter
        """
        self._config = config
        self._probes = list(probes)
        self._static_cameras = static_cameras
        self._movable_cameras = movable_cameras
        self._light_controller = light_controller
        self._target_power_controller = target_power_controller
        self._signal_multiplexer = signal_multiplexer
        self._picoscope = picoscope
        self._uart_interface_adapter = uart_interface_adapter

        # Sort the probes by order index
        self._probes.sort(key=lambda probe: probe.config.order_index)
        self._probes = tuple(self._probes)

    @property
    def id(self) -> int:
        """
        The unique identifier of the PROBoter
        """
        return self._config.id

    @property
    def name(self) -> str:
        """
        The displayable name of the PROBoter
        """
        return self._config.name

    @property
    def probes(self) -> Sequence[Probe]:
        """
        The PROBoter probes
        """
        return self._probes

    @property
    def static_cameras(self) -> Sequence[StaticCamera]:
        """
        The PROBoter's static camera systems
        """
        return tuple(self._static_cameras)

    @property
    def movable_cameras(self) -> Sequence[MovableCamera]:
        """
        The PROBoter's movable camera systems
        """
        return tuple(self._movable_cameras)

    @property
    def cameras(self) -> Sequence[Camera]:
        """
        The PROBoter's camera systems (static and movable)
        """
        cameras = []
        cameras += self.static_cameras
        cameras += self.movable_cameras
        return tuple(cameras)

    @property
    def light_controller(self) -> Optional[LightController]:
        """
        The PROBoter system light controller if one exists
        """
        return self._light_controller

    @property
    def uart_interface_adapter(self) -> Optional[UartInterfaceAdapter]:
        """
        The PROBoter system's integrated target UART interface adapter
        """
        return self._uart_interface_adapter

    @property
    def target_power_controller(self) -> Optional[TargetPowerController]:
        """
        The PROBoter system power switch controller if one exists
        """
        return self._target_power_controller

    @property
    def signal_multiplexer(self) -> Optional[SignalMultiplexer]:
        """
        The PROBoter system signal multiplexer
        """
        return self._signal_multiplexer

    @property
    def picoscope(self) -> Optional[Picoscope]:
        """
        The PROBoter system picoscope
        """
        return self._picoscope

    @property
    def status(self) -> ProboterStatus:
        """
        Return the PROBoter status
        """
        probes = [probe.probe_type.value for probe in self.probes]
        static_cameras = [idx for idx, cam in enumerate(self.static_cameras)]
        movable_cameras = [idx for idx, cam in enumerate(self.movable_cameras)]
        has_light_controller = self.light_controller is not None
        has_picoscope = self.picoscope is not None
        has_signal_multiplexer = self.signal_multiplexer is not None
        has_uart_adapter = self.uart_interface_adapter is not None
        has_target_power_controller = self.target_power_controller is not None

        return ProboterStatus(id=self.id,
                              name=self.name,
                              probes=probes,
                              static_cameras=static_cameras,
                              movable_cameras=movable_cameras,
                              has_light_controller=has_light_controller,
                              has_picoscope=has_picoscope,
                              has_signal_multiplexer=has_signal_multiplexer,
                              has_uart_adapter=has_uart_adapter,
                              has_target_power_controller=has_target_power_controller)

    async def start(self) -> None:
        """
        Startup the hardware components
        """
        self.log.info("Starting up camera systems...")
        for camera in self.cameras:
            await camera.start()

        self.log.info("Starting up probes...")
        for probe in self.probes:
            await probe.start()

        if self.light_controller is not None:
            self.log.info("Starting up light controller")
            await self.light_controller.start()

        if self.target_power_controller is not None:
            self.log.info("Starting up target power controller")
            await self.target_power_controller.start()

        if self.signal_multiplexer is not None:
            self.log.info("Starting up signal multiplexer")
            await self.signal_multiplexer.start()

        if self.uart_interface_adapter is not None:
            self.log.info("Starting up signal UART interface polling")
            await self.uart_interface_adapter.start()

    async def stop(self) -> None:
        """
        Shutdown the hardware components
        """
        self.log.info("Stopping camera systems...")
        for camera in self.cameras:
            await camera.stop()

        self.log.info("Stopping probes...")
        for probe in self.probes:
            await probe.stop()

        if self.light_controller is not None:
            self.log.info("Stopping light controller")
            await self.light_controller.stop()

        if self.target_power_controller is not None:
            self.log.info("Stopping target power controller")
            await self.target_power_controller.stop()

        if self.signal_multiplexer is not None:
            self.log.info("Stopping signal multiplexer")
            await self.signal_multiplexer.stop()

        if self.uart_interface_adapter is not None:
            self.log.info("Stopping UART interface polling")
            await self.uart_interface_adapter.stop()

    async def home(self) -> None:
        """
        Home all components of the PROBoter hardware

        After this, the hardware platform is in a known state.
        First, the two left probes (2.1 and 2) are homed. Then,
        the two right probes (1.1 and 1) are homed. After each
        homing, the probe is also moved to it's safety position
        """
        # 1. Home inner probe Z axis
        await asyncio.gather(self.get_probe_by_type(ProbeType.P1).home(AxisDirection.Z),
                             self.get_probe_by_type(ProbeType.P2).home(AxisDirection.Z))

        # 2. Home outer probe Z axis
        await asyncio.gather(self.get_probe_by_type(ProbeType.P11).home(AxisDirection.Z),
                             self.get_probe_by_type(ProbeType.P21).home(AxisDirection.Z))

        # 3. Home all Y axes
        await asyncio.gather(
            self.get_probe_by_type(ProbeType.P1).home(AxisDirection.Y),
            self.get_probe_by_type(ProbeType.P2).home(AxisDirection.Y),
            self.get_probe_by_type(ProbeType.P11).home(AxisDirection.Y),
            self.get_probe_by_type(ProbeType.P21).home(AxisDirection.Y))

        # 3. Home outer probe X axis
        await asyncio.gather(self.get_probe_by_type(ProbeType.P11).home(AxisDirection.X),
                             self.get_probe_by_type(ProbeType.P21).home(AxisDirection.X))

        # 4. Home inner probe X axis
        await asyncio.gather(self.get_probe_by_type(ProbeType.P1).home(AxisDirection.X),
                             self.get_probe_by_type(ProbeType.P2).home(AxisDirection.X))

    async def home_probe(self, probe: Probe) -> None:
        """
        Home a single probe

        After homing the probe is moved to its safety position

        :param probe: Probe to home
        :type probe: Probe
        """
        await probe.home()
        await probe.move_to_safety_position()

    def move_camera(self, camera: MovableCamera, position: np.ndarray,
                    feed: float = 1000, is_global: bool = False) -> None:
        """
        Move a movable camera to a given position

        This is a SAFE command with collision avoidance activated!

        :param camera: Camera to move
        :type camera: MovableCamera
        :param position: Position the camera should be moved to as
                         numpy 2D vector
        :type position: np.ndarray
        :param feed: Movement feed in mm/min, defaults to 1000
        :type feed: float
        :param is_global: Whether the target coordinates are in the local axes
                          controller system (False) or in the common global
                          system (True)
        """
        # Input validation
        assert camera in self.movable_cameras, \
            'camera does not belong to PROBoter instance'
        assert feed > 0, 'feed must be a value greater than zero'
        assert isinstance(position, np.ndarray) and position.shape == (2,), \
            'position must be a 2D vector'

        # TODO Implement collision avoidance check here!!
        if is_global:
            raise NotImplementedError()
        camera.move(position, feed)

    def home_camera(self, camera: MovableCamera) -> None:
        """
        Home a movable camera to a given position

        This is a SAFE command with collision avoidance activated!

        :param camera: Camera to home
        :type camera: MovableCamera
        """
        # Input validation
        assert camera in self.movable_cameras, \
            'camera does not belong to PROBoter instance'
        camera.home()

    async def clear_probing_area(self) -> None:
        """
        Clear the probing area

        This command moves all probes safely to their parking positions
        """
        probe_positions = {}
        for probe_type in ProbeType:
            probe = self.get_probe_by_type(probe_type)
            probe_positions[probe] = probe.map_local_to_global_point(
                probe.safety_position)
        await self.move_probes(probe_positions)

    async def clear_area_for_probe(self, probe: Probe) -> None:
        """
        Move all probes left of the given probe to their leftmost safety
        positions. All probes right of the given probe are moved to their
        rightmost safety positions.

        :param probe: Probe for which the are should be cleared. The remaining
                      probes are moved to their crash-safe safety positions
        :type probe: Probe
        """
        self.log.debug("Clearing area for probe %s", probe.probe_type)
        probe_positions = {}
        idx = self.probes.index(probe)
        for tmp_probe in self.probes[:idx]:
            probe_positions[tmp_probe] = tmp_probe.positive_x_safety_position
        for tmp_probe in self.probes[idx + 1:]:
            probe_positions[tmp_probe] = tmp_probe.negative_x_safety_position
        await self.move_probes(probe_positions)

    async def move_probes(self, destinations_map: Dict[Probe, np.ndarray],
                          xy_feed: float = 1000,
                          drop_feed: float = 2000,
                          soft_drop: bool = True) -> bool:
        """
        Moves probes according to destinations mapped to them in destinations_map.

        This is a SAFE command with collision avoidance.

        :param destinations_map: A dictionary mapping probes to the destinations
                                 they should be moved to.
        :type destinations_map: Dict[Probe, np.ndarray]
        :param xy_feed: Probe speed in the xy-plane.
        :type xy_feed: float
        :param drop_feed: Probe speed in z-direction.
        :type drop_feed: float
        :param soft_drop: Option to drive the last part in z-direction at a lower speed to
        decrease the impact on the probes.
        :type soft_drop: bool
        :return: true iff the movement is valid and could be executed, false otherwise
        :rtype: bool
        """
        self.log.info("Moving probes to %s",
                      {probe.probe_type: dest for probe,
                       dest in destinations_map.items()})

        coordinator = MoveCoordinator(self.probes,
                                      plane_speed=xy_feed,
                                      drop_speed=drop_feed)
        try:
            all_movements = coordinator.coordinate_movement(destinations_map,
                                                            soft_drop)
        except InvalidDestinationsError as exc:
            self.log.error("Probes could not be moved: %s", exc)
            return False

        for parallel_movements in all_movements:
            tasks = [movement.probe.move_to_global_position(movement.destination,
                                                            movement.feed)
                     for movement in parallel_movements]
            await asyncio.gather(*tasks)

        return True

    def get_probe_by_type(self, probe_type: ProbeType) -> Optional[Probe]:
        """
        Get a probe by its type / location in the PROBoter hardware

        :param probe_type: Probe type to look for
        :type probe_type: ProbeType
        :return: The probe in the current setup of this type or None if no
                 such probe is defined
        :rtype: Optional[Probe]
        """
        probes = [probe for probe in self.probes
                  if probe.config.probe_type == probe_type]
        if len(probes) > 0:
            return probes[0]
        return None

    @ staticmethod
    def map_camera_to_probe_points(camera_points: np.ndarray, z: float,
                                   camera: Camera, probe: Probe) -> np.ndarray:
        """
        Convert a point in the camera system to the corresponding
        point in the probe / axes local system

        :param camera_points: 2D points in the camera coordinate system
                              as n x 2 numpy array
        :param z: The distance of the probe point to the image plane in mm
        :param camera: The camera in whose image coordinate system the points are defined
        :param probe: The probe in whose coordinate system the points will be transformed
        :return: The corresponding 3D points in the probe coordinate system
                 as n x 3 numpy array
                 Important: The z axis coordinate is set to the current
                            probe z coordinate!
        """
        ref_points = camera.map_image_to_global_points(camera_points, z)
        return probe.map_global_to_local_points(ref_points)

    @ staticmethod
    def map_probe_to_camera_points(probe_points: np.ndarray, probe: Probe,
                                   camera: Camera) -> np.ndarray:
        """
        Convert a point in the probe / axes local system to the corresponding
        point in the camera image plane

        :param probe_points: 3D points in the probe coordinate system
                             as n x 3 numpy array
        :param probe: The probe in whose coordinate system the points are defined
        :param camera: The camera to whose image coordinate system the points will be transformed
        :return: The corresponding 2D points in the camera image plane
                  as n x 2 numpy array
        """
        ref_points = probe.map_local_to_global_points(probe_points)
        return camera.map_global_to_image_points(ref_points)
