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
from typing import List
from dataclasses import dataclass

import numpy as np

from proboter.model import ProbeType
from proboter.hardware import Proboter
from proboter.storage import Pin

from .task import Task


@dataclass
class MeasureVoltageSignalsParameter:
    """
    Voltage signal measurement parameters
    """
    # ID of the current PCB
    pcb: int
    # List of pin / pad IDs to probe
    pins: List[int]
    # Trigger level in mV
    trigger_level: float
    # Time resolution in nanoseconds
    time_resolution: float
    # Measurement duration in seconds
    duration: float
    # Probing point Z offset
    z_offset: float


@dataclass
class MeasureVoltageSignalsResult:
    """
    Voltage signal measurement results
    """


class MeasureVoltageSignalsTask(
        Task[MeasureVoltageSignalsParameter,
             MeasureVoltageSignalsResult]):
    """
    Task to measure voltage levels at given number of pins / pads
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: MeasureVoltageSignalsParameter,
                 proboter: Proboter,):
        """
        Initialize a new electrical connectivity probing task
        """
        super().__init__("MeasureVoltageSignals", params)
        self._proboter = proboter

    async def run(self) -> MeasureVoltageSignalsResult:
        """
        Trigger voltage level measurements at the given pins / pads

        : return: Measurement results
        : rtype: MeasureVoltageSignalsResult
        """
        self.log.info("Start voltage measurement task")

        # Fetch the corresponding pins from the database
        self.log.info("Query pin / pad data")
        pins = []
        for pin_id in self.params.pins:
            pins.append(await Pin.get_by_id(self.params.pcb, pin_id))

        # Sort the pins according to their X position
        pins = sorted(pins, key=lambda p: p.center[0])

        # Select the probes to use
        probe_left = self._proboter.get_probe_by_type(ProbeType.P1)
        probe_right = self._proboter.get_probe_by_type(ProbeType.P2)
        safety_position_left = probe_left.map_local_to_global_point(
            probe_left.safety_position)
        safety_position_right = probe_right.map_local_to_global_point(
            probe_right.safety_position)

        def adjusted_pin_center(pin: Pin) -> np.ndarray:
            return np.array([pin.center[0],
                             pin.center[1],
                             self.params.z_offset])

        # Probe from the outermost pins to the inner
        while len(pins) > 0:
            measurement_pose = {}
            # Select the left pin to probe
            pin_left = pins.pop(0)
            measurement_pose[probe_left] = adjusted_pin_center(pin_left)

            # Select the right pin - if any - to probe
            pin_right = pins.pop(-1) if len(pins) > 0 else None
            measurement_pose[probe_right] = adjusted_pin_center(pin_right)\
                if pin_right is not None \
                else safety_position_right

            # Position the probes
            await self._proboter.move_probes(measurement_pose, xy_feed=2000, soft_drop=True)

            # TODO Replace fixed delay with actual picoscope measurement!!
            await asyncio.sleep(self.params.duration)

        # Finally move the probes to their respective safety positions
        await self._proboter.move_probes({
            probe_left: safety_position_left,
            probe_right: safety_position_right
        }, xy_feed=2000, soft_drop=False)

        return MeasureVoltageSignalsResult()
