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
from proboter.model import ProboterConfig
from proboter.hardware import Proboter, ProboterFactory

from .simulation_probe import SimulationProbe
from .simulation_light_controller import SimulationLightController
from .simulation_signal_multiplexer import SimulationSignalMultiplexer
from .simulation_uart_interface_adapter import SimulationUartInterfaceAdapter
from .simulation_target_power_controller import SimulationTargetPowerController
from .simulation_static_camera import SimulationStaticCamera
from .simulation_movable_camera import SimulationMovableCamera


class SimulationProboterFactory(ProboterFactory):
    """
    Factory that creates PROBoter hardware simulation instances

    The factory installs callbacks on all created hardware
    components and publishes them on a given event bus.
    """

    log = logging.getLogger(__module__)

    def __init__(self, event_bus: EventBus) -> None:
        """
        Initialize a PROBoter simulation factory

        :param event_bus: Internal event bus that is used to register
                          hardware events
        :type event_bus: EventBus
        """
        ProboterFactory.__init__(self)
        # The central event bus
        self._event_bus = event_bus

    async def create_from_config(self, config: ProboterConfig,
                                 autostart: bool = True) -> Proboter:
        """
        Create a PROBoter instance from a given configuration

        :param config: The Proboter configuration to use
        :type config: ProboterConfig
        :param autostart: Whether to automatically start the newly created
                          PROBoter instance, defaults to True
        :type autostart: bool
        :return: Created PROBoter instance
        :rtype: Proboter
        """
        # Fetch the PROBoter configuration
        proboter = await self._create_proboter_from_config(config)

        # Start the new PROBoter instance
        if autostart:
            proboter.start()

        return proboter

    async def _create_proboter_from_config(self, config: ProboterConfig) -> Proboter:
        """
        Create a PROBoter instance from a configuration

        First, the probes are brought back. In the next step, all the cameras
        are instantiated. The axes controller objects are cached and reused
        if they are referenced by probes and cameras

        :param config: The PROBoter configuration to used
        :type config: ProboterConfig
        :return: The created PROBoter instance (not started yet!!)
        :rtype: Proboter
        """

        self.log.debug("Creating PROBoter from config %d", config.id)

        probes = []
        static_cameras = []
        movable_cameras = []
        light_controller = None
        target_power_controller = None
        picoscope = None
        uart_interface_adapter = None
        multiplexer = None

        # Restore all probes
        self.log.debug("Restoring probes for PROBoter with ID %d",
                       config.id)
        async for probe_config in config.probes:
            # Create the probe
            self.log.debug("Instantiating probe with ID %d", probe_config.id)
            probe = SimulationProbe(config=probe_config,
                                    event_bus=self._event_bus)
            probes.append(probe)

        # Restore all cameras
        self.log.debug("Restoring static cameras for PROBoter with ID %d",
                       config.id)
        camera_index = 0
        async for camera_config in config.static_cameras:
            self.log.debug("Creating STATIC camera with ID %d",
                           camera_config.id)
            camera = SimulationStaticCamera(camera_config=camera_config,
                                            camera_index=camera_index,
                                            event_bus=self._event_bus)
            static_cameras.append(camera)
            camera_index += 1

        self.log.debug("Restoring movable cameras for PROBoter with ID %d",
                       config.id)
        async for camera_config in config.movable_cameras:
            self.log.debug("Creating MOVABLE camera with ID %d",
                           camera_config.id)
            camera = SimulationMovableCamera(camera_config=camera_config,
                                             event_bus=self._event_bus)
            movable_cameras.append(camera)

        # Restore the signal multiplexer board (if any)
        multiplexer_config = await config.signal_multiplexer
        if multiplexer_config is None:
            self.log.info("PROBoter has no multiplexer board configured")
        else:
            self.log.debug("Restoring signal multiplexer with ID %d",
                           multiplexer_config.id)
            multiplexer = SimulationSignalMultiplexer(
                config=multiplexer_config,
            )

        # Restore the light controller
        self.log.debug("Restoring light controller")
        light_controller = SimulationLightController(self._event_bus)

        # Restore the target power controller
        self.log.debug("Restoring target power controller")
        target_power_controller_config = await config.target_power_controller
        target_power_controller = SimulationTargetPowerController(
            target_power_controller_config, self._event_bus)

        # Restore the UART Interface Adapter
        async def emit_uart_data(event):
            await self._event_bus.emit_event(event)

        uart_adapter_config = await config.uart_interface_adapter
        if uart_adapter_config is None:
            self.log.info("PROBoter has no UART interface adapter configured")
        else:
            self.log.debug("Restoring UART interface adapter with ID %d",
                           uart_adapter_config.id)
            uart_interface_adapter = \
                SimulationUartInterfaceAdapter(config=uart_adapter_config,
                                               on_new_uart_data=emit_uart_data)

        # TODO: Add simulated picoscope here!

        # Finally set up a new PROBoter instance
        proboter = Proboter(config=config,
                            probes=probes,
                            static_cameras=static_cameras,
                            movable_cameras=movable_cameras,
                            light_controller=light_controller,
                            target_power_controller=target_power_controller,
                            signal_multiplexer=multiplexer,
                            picoscope=picoscope,
                            uart_interface_adapter=uart_interface_adapter)
        return proboter
