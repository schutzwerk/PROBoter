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
import time
from typing import List, Optional
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from proboter.model import ProbeType
from proboter.hardware import Proboter, Probe
from proboter.storage import ElectricalNet
from proboter.fields import NumpyArray

from .task import Task
from .utils import NetworkManager


@dataclass
class FakePin:
    """
    A single pin
    """
    # Unique ID of the pin
    id: Optional[int] = None
    # Pin center as 3D vector
    center: NumpyArray = Field(np_shape=3)


@dataclass
class ProbePartyParameter:
    """
    Demo mode / probe party parameters
    """
    # Probing feed in mm/min
    feed: float = 1000.0
    # Drop feed in Z direction
    drop_feed: float = 2000.0
    # Offset in Z direction in the global coordinate system
    z_offset: float = -5.0


@dataclass
class ProbePartyResult:
    """
    Demo mode / probe party results
    """


class ProbePartyTask(Task[ProbePartyParameter, ProbePartyResult]):
    """
    Task to let the probes measure different points in an endless loop for demonstration purposes
    """

    fakePinList = [
        FakePin(1, np.array([20.0, 70.0, -5.0])),
        FakePin(1, np.array([-15.0, 35.0, -5.0])),
        FakePin(1, np.array([-35.0, 70.0, -5.0])),
        FakePin(1, np.array([15.0, 39.0, -5.0])),
        FakePin(1, np.array([5.0, -20.0, -5.0])),
        FakePin(1, np.array([25.0, -44.0, -5.0])),
        FakePin(1, np.array([-30.0, -50.0, -5.0])),
        FakePin(1, np.array([-25.0, -14.0, -5.0])),
        FakePin(1, np.array([-31.0, 24.0, -5.0])),
        FakePin(1, np.array([-10.0, 10.0, -5.0])),
    ]

    log = logging.getLogger(__name__)

    def __init__(self, params: ProbePartyParameter,
                 proboter: Proboter,):
        """
        Initialize a new electrical connectivity probing task
        """
        super().__init__("ProbeParty", params)
        self._proboter = proboter

    async def run(self) -> ProbePartyResult:
        """
        Probe the given set of pins / pads for electrical connectivity

        : return: Probing results
        : rtype: ProbeElectricalConnectivityResult
        """

        try:
            # Check maximum values for feed and z_offset
            self.params.feed = max(0, self.params.feed)
            self.params.feed = min(self.params.feed, 5000)

            self.params.z_offset = max(-10.0, self.params.z_offset)
            self.params.z_offset = min(self.params.z_offset, -3.0)

            self.params.drop_feed = 6000.0

            pins = self.fakePinList[:]

            self.log.info("Fetching already defined electrical networks")

            self.log.info("Allocating probes for probing")
            fake_probes = [ProbeType.P1, ProbeType.P11,
                           ProbeType.P2, ProbeType.P21]
            probes = [self._proboter.get_probe_by_type(probe_type)
                      for probe_type in fake_probes]
            probes.sort(key=lambda p: p.probe_type.to_order_index())

            networks = await self.find_networks(pins, probes)

            self.log.info("Finished electrical connectivity probing: %s",
                          networks)

            # Return nothing
            return ProbePartyResult()

        except asyncio.CancelledError as exc:
            await self._proboter.clear_probing_area()
            raise exc

    async def find_networks(self, pins: List[FakePin], probes: List[Probe]) -> List[ElectricalNet]:
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

        counter = 10
        while counter > 0:
            counter -= 1
            # For each point A, probe each point left of it against point A
            for i in range(pin_count - 1):
                self.log.debug("Connectivity run %d of %d",
                               i + 1, pin_count - 1)
                master_pin = pins[i]
                remaining = pins[i + 1:]
                await self._measure_points_against_master(probes,
                                                          master_pin,
                                                          remaining)
        # Restore the initial PROBoter pose
        self.log.debug("Restoring initial PROBoter pose")
        await self._proboter.move_probes(proboter_initial_pose, xy_feed=self.params.feed,
                                         drop_feed=self.params.drop_feed, soft_drop=False)

        # Extract networks from network manager
        return network_manager.extract_networks()

    async def _measure_points_against_master(self, probes: List[Probe],
                                             master_pin: FakePin,
                                             remaining_pins: List[FakePin]) -> None:
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
        """
        self.log.debug("Probe master pin %d and %d slave pins",
                       master_pin.id, len(remaining_pins))

        master_probe = probes[0]
        remaining_probes = probes[1:]

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
                                             drop_feed=self.params.drop_feed,
                                             soft_drop=True)

            # Wait a second as "Fake Measurement"
            time.sleep(0.5)
