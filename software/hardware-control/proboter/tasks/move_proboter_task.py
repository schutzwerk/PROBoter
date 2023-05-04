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
from dataclasses import dataclass
from typing import List

from pydantic import Field

from proboter.model import ProbeType
from proboter.hardware import Proboter
from proboter.fields import NumpyArray

from .task import Task


@dataclass
class ProbeMovement:
    """
    Movement parameters for a single probe
    """
    # Probe
    probe: ProbeType
    # Movement destination
    position: NumpyArray = Field(np_shape=3)
    # Whether the position is in global coordinates
    is_global: bool = True
    # Movement feed im m/min
    feed: float = 1000
    # Whether to 'soft drop' the probe
    use_soft_drop: bool = True


@dataclass
class MoveProboterParameter:
    """
    PROBoter move task parameter
    """
    probes: List[ProbeMovement]


@dataclass
class MoveProboterResult:
    """
    PROBoter move task result
    """


class MoveProboterTask(
        Task[MoveProboterParameter, MoveProboterResult]):
    """
    Task to move one or many of the PROBoter's electrical probes to new positions
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: MoveProboterParameter,
                 proboter: Proboter):

        super().__init__("MoveProboter", params)

        self._proboter = proboter

    async def run(self) -> MoveProboterResult:
        """
        Move one or multiple of the PROBoter's electrical probes

        :rtype: MoveProboterResult
        """
        self.log.info("Starting PROBoter movement")

        if len(self.params.probes) < 1:
            self.log.info("No probes to move")
            return MoveProboterResult()

        # Movement data conversion
        destination_map = {}
        for probe_movement in self.params.probes:
            probe = self._proboter.get_probe_by_type(probe_movement.probe)
            destination = probe_movement.position if probe_movement.is_global \
                else probe.map_local_to_global_point(probe_movement.position)
            destination_map[probe] = destination

        # Trigger the movement
        await self._proboter.move_probes(destination_map,
                                         self.params.probes[0].feed,
                                         self.params.probes[0].use_soft_drop)

        return MoveProboterResult()
