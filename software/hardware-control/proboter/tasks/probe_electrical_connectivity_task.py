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
from typing import List
from dataclasses import dataclass

from proboter.model import ProbeType
from proboter.hardware import Proboter, Probe, SignalMultiplexerChannelDigitalLevel
from proboter.storage import Pin, ElectricalNet

from .task import Task
from .utils import NetworkManager


@dataclass
class ProbeElectricalConnectivityParameter:
    """
    Electrical connectivity probing parameters
    """
    # ID of the current PCB
    pcb: int
    # List of pin / pad IDs to probe
    pins: List[int]
    # Probes to use for electrical connectivity probing
    probes: List[ProbeType]
    # Probing feed in mm/min
    feed: float = 1000.0
    # Offset in Z direction in the global coordinate system
    z_offset = 0.0


@dataclass
class ProbeElectricalConnectivityResult:
    """
    Electrical connectivity probing results
    """


class ProbeElectricalConnectivityTask(
        Task[ProbeElectricalConnectivityParameter,
             ProbeElectricalConnectivityResult]):
    """
    Task to probe a given set of pins / pads for electrical connectivity
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: ProbeElectricalConnectivityParameter,
                 proboter: Proboter,):
        """
        Initialize a new electrical connectivity probing task
        """
        super().__init__("ProbeElectricalConnectivity", params)
        self._proboter = proboter

    async def run(self) -> ProbeElectricalConnectivityResult:
        """
        Probe the given set of pins / pads for electrical connectivity

        : return: Probing results
        : rtype: ProbeElectricalConnectivityResult
        """
        self.log.info("Fetching pin data from storage")
        pins = []
        for pin_id in self.params.pins:
            pin = await Pin.get_by_id(self.params.pcb, pin_id)
            pins.append(pin)

        self.log.info("Allocating probes for probing")
        probes = [self._proboter.get_probe_by_type(probe_type)
                  for probe_type in self.params.probes]
        probes.sort(key=lambda p: p.probe_type.to_order_index())

        networks = await self.find_networks(pins, probes)

        self.log.info("Finished electrical connectivity probing: %s", networks)

        # Return network with pin ids
        # TODO Fix network extraction and storage!!
        return ProbeElectricalConnectivityResult()

    async def find_networks(self, pins: List[Pin], probes: List[Probe]) -> List[ElectricalNet]:
        """
        This method measures each point against each other using the multiplexer.
        It returns a list of network instances.
        """
        self.log.debug("Start probing %d pins for electrical connectivity",
                       len(pins))
        # Network manager
        network_manager = NetworkManager()

        # Sort points from right to left
        pins = sorted(pins, key=lambda p: p.center[0])
        pin_count = len(pins)

        # Store the current PROBoter pose
        self.log.debug("Saving current PROBoter pose")
        proboter_initial_pose = {}
        for probe in probes:
            proboter_initial_pose[probe] = probe.position_global

        # For each point A, probe each point left of it against point A
        for i in range(pin_count - 1):
            self.log.debug("Connectivity run %d of %d", i + 1, pin_count - 1)
            master_pin = pins[i]
            remaining = pins[i + 1:]
            await self._measure_points_against_master(probes,
                                                      master_pin,
                                                      remaining,
                                                      network_manager)

        # Restore the initial PROBoter pose
        self.log.debug("Restoring initial PROBoter pose")
        await self._proboter.move_probes(proboter_initial_pose, xy_feed=self.params.feed,
                                         soft_drop=False)

        # Extract networks from network manager
        return network_manager.extract_networks()

    async def _measure_points_against_master(self, probes: List[Probe],
                                             master_pin: Pin,
                                             remaining_pins: List[Pin],
                                             network_manager: NetworkManager) -> None:
        """
        Measures all pins in remaining_pins against the master pin. This is done
        by pulling the master pin with the multiplexer and iterating over all remaining
        pins, measuring their state.
        Connections are logged into the network_manager.

        :param master_pin: The pin to measure all other pins against
        :type master_pin: Pin
        :param remaining_pins: The remaining pins which are to be measured
                               against the master_pin
        :type remaining_pins: List[Pin]
        :param network_manager: A PcbNetworkManager instance for handling
                                determined connections between pins.
        :type network_manager: PcbNetworkManager
        """
        self.log.debug("Probe master pin %d and %d slave pins",
                       master_pin.id, len(remaining_pins))

        master_probe = probes[0]
        remaining_probes = probes[1:]
        multiplexer = self._proboter.signal_multiplexer
        master_pulled = False

        # Iterate over remaining points and probe against
        # master probe in tuples of (probe count - 1)
        while len(remaining_pins) > 0:
            # Find next (probe count - 1) points which haven't been probed
            # against master_point
            self.log.debug("Assign probes to pins")
            pin_probe_map = {}
            for probe in remaining_probes:
                if len(remaining_pins) < 1:
                    break
                pin = remaining_pins.pop(0)
                # TODO Fix this in the future!!
                # if network_manager.connection_state(master_pin, pin) ==
                # network_manager.UNKNOWN:
                pin_probe_map[probe] = pin

            # If no points were found, probing against this master pin is over
            if len(pin_probe_map) < 1:
                break

            # Move to positions
            self.log.debug("Moving probes to pins")
            master_pin_center = master_pin.center.copy()
            master_pin_center[2] = self.params.z_offset
            destinations_map = {master_probe: master_pin_center}
            for probe, pin in pin_probe_map.items():
                destinations_map[probe] = pin.center.copy()
                destinations_map[probe][2] = self.params.z_offset
            await self._proboter.move_probes(destinations_map,
                                             xy_feed=self.params.feed,
                                             soft_drop=True)

            if not master_pulled:
                # Pull master_probe
                await multiplexer.release_all()
                await multiplexer.pull_probe(master_probe)
                master_probe_state = SignalMultiplexerChannelDigitalLevel.HIGH

            # Measure points against master
            self.log.debug("Measuring electrical connectivity")
            for probe, pin in pin_probe_map.items():
                probe_state = await multiplexer.test_probe(probe)
                connected = probe_state == master_probe_state
                self.log.debug("Test result for pins %d / %d (probe %s): %s",
                               pin.id, master_pin.id, probe.probe_type.name,
                               probe_state)
                network_manager.set_connected(master_pin.id, pin.id, connected)
