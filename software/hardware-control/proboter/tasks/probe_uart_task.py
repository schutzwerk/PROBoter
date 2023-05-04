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
from dataclasses import dataclass

from proboter.hardware import Proboter
from proboter.storage import Pin

from .task import Task


@dataclass
class UartProbingMoveTaskParameter:
    """
    UART interface probing move parameters
    """
    baudrate: int
    pcb: int
    rx_pin: int
    tx_pin: int


@dataclass
class UartProbingMoveTaskResult:
    """
    UART interface probing move result
    """


class UartProbingMoveTask(Task[UartProbingMoveTaskParameter, UartProbingMoveTaskResult]):
    """
    UART probing preparation task

    This task does the following steps in preparation of an UART probing:
    - Select two appropriate probes for the probing operation
    - Position the probes at the given locations
    - Route the signals to the correct outputs of the signal multiplexer
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: UartProbingMoveTaskParameter,
                 proboter: Proboter):

        super().__init__("UartProbingMove", params)

        self.proboter = proboter

    async def run(self) -> UartProbingMoveTaskResult:
        """
        Setup the PROBoter hardware to probe a UART interface

        - The routine moves the corresponding probes to the RX / TX probing point
        locations
        - The signal multiplexer is configured to route the probe signals to
        the connected UART interface adapter
        - The UART interface adapter is initially configured with the
        provided baud rate
        - The UART interface adapter connection is opened

        :rtype: UartProbingMoveTaskResult
        """
        self.log.info("Starting UART interface probing")

        # Fetching pin coordinates from storage service
        self.log.info("Fetching pin coordinates")
        rx_pin = await Pin.get_by_id(self.params.pcb, self.params.rx_pin)
        tx_pin = await Pin.get_by_id(self.params.pcb, self.params.tx_pin)

        # Close a previously opened UART connection
        if self.proboter.uart_interface_adapter.status.open:
            await self.proboter.uart_interface_adapter.close()

        # Fetch the probes for the RX and TX pins
        rx_probe_types = []
        rx_probe_types.append(await self.proboter.signal_multiplexer.get_probe_type_by_channel(
            self.proboter.uart_interface_adapter.config.rx_multiplexer_channel_1))
        rx_probe_types.append(await self.proboter.signal_multiplexer.get_probe_type_by_channel(
            self.proboter.uart_interface_adapter.config.rx_multiplexer_channel_2))
        rx_probe_types.sort(key=lambda pt: pt.to_order_index())
        rx_probes = [self.proboter.get_probe_by_type(probe_type)
                     for probe_type in rx_probe_types]

        tx_probe_types = []
        tx_probe_types.append(await self.proboter.signal_multiplexer.get_probe_type_by_channel(
            self.proboter.uart_interface_adapter.config.tx_multiplexer_channel_1))
        tx_probe_types.append(await self.proboter.signal_multiplexer.get_probe_type_by_channel(
            self.proboter.uart_interface_adapter.config.tx_multiplexer_channel_2))
        tx_probe_types.sort(key=lambda pt: pt.to_order_index())
        tx_probes = [self.proboter.get_probe_by_type(probe_type)
                     for probe_type in tx_probe_types]

        # Select the probes depending on the X position of the RX and TX pins
        probe_idx = 0 if rx_pin.center[0] >= tx_pin.center[0] else 1
        rx_probe = rx_probes[probe_idx]
        tx_probe = tx_probes[probe_idx]
        self.log.debug("Using probe %s for RX pin probing",
                       rx_probe.probe_type)
        self.log.debug("Using probe %s for TX pin probing",
                       tx_probe.probe_type)

        # Position probes
        self.log.debug("Positioning probes")
        proboter_pose = {
            rx_probe: rx_pin.center,
            tx_probe: tx_pin.center,
        }
        await self.proboter.move_probes(proboter_pose, soft_drop=True)

        # Open the UART connection
        self.log.debug("Opening UART connection with baud rate %d",
                       self.params.baudrate)

        # Hopefully, after 2 seconds no more bogus data is
        # emitted by the UART interface
        await asyncio.sleep(2)
        await self.proboter.uart_interface_adapter.open(self.params.baudrate)

        return UartProbingMoveTaskResult()
