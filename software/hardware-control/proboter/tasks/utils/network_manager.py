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
from enum import Enum
from typing import List
from collections import defaultdict

from disjoint_set import DisjointSet

from proboter.storage import ElectricalNet


class ConnectionState(int, Enum):
    """
    Pin connection state
    """
    NOT_CONNECTED = 0
    CONNECTED = 1
    UNKNOWN = -1


class NetworkManager:
    """
    This class can be used to manage and query connections between points.

    Using a disjoint-set for connected and dictionaries for not connected
    points, it can determine if two points are connected, not_connected or
    unknown in practically constant time.

    Contemplate three points 1, 2 and 3, where he relationship between (1,2)
    and (2,3) is known; the relationship between (1,3) is queried.
    Three cases arise:

    Case 1: (1,2) and (2,3) are connected, then (1,3) are also connected. This
            is reflected in the disjoint set, since find(1) == find(3)

    Case 2: (1,2) are connected, (2,3) are not. find(3) is in the set of
            not_connected points of find(2). Additionally 1 and 2 are connected,
            therefore find(1) == find(2). The relationship (1,3) can then be
            established by testing whether find(3) is in not_connected[find(1)]

    Case 3: Neither (1,2) or (2,3) are connected. In this case the relationship
            (1,3) cannot be deduced
    """

    log = logging.getLogger(__module__)

    def __init__(self):
        self._ds: DisjointSet = DisjointSet()
        self._not_connected = defaultdict(set)

    def clear(self) -> None:
        """
        Reset the internal state
        """
        self._ds = DisjointSet()
        self._not_connected = defaultdict(set)

    def connection_state(self, pin1: int, pin2: int) -> ConnectionState:
        """
        This method attempts to deduce whether point1 and point 2 are connected.

        :param pin1: The first pin
        :param pin2: The second pin
        :return: Pin connection state
        """
        find1 = self._ds.find(pin1)
        find2 = self._ds.find(pin2)

        if find1 == find2:
            return ConnectionState.CONNECTED

        if find2 in self._not_connected[find1] or find1 in self._not_connected[find2]:
            return ConnectionState.NOT_CONNECTED

        return ConnectionState.UNKNOWN

    def set_connected(self, pin1: int, pin2: int,
                      connection: bool = True) -> None:
        """
        Sets the connection state of the given pins to the value of connection.

        :param pin1: The first pin
        :param pin2: The second pin
        :param connection: The value to set the connection to
        """
        if connection:
            self.connect(pin1, pin2)
        else:
            self.disconnect(pin1, pin2)

    def connect(self, pin1: int, pin2: int) -> None:
        """
        Marks the given pins as connected and updates the data structures accordingly.

        :param pin1: The first pin
        :param pin2: The second pin
        """
        self.log.debug("Connecting pin %d and %d", pin1, pin2)
        find1 = self._ds.find(pin1)
        find2 = self._ds.find(pin2)

        self._ds.union(find1, find2)
        find = self._ds.find(find1)

        total = self._not_connected[find1].union(self._not_connected[find2])
        self._not_connected[find] = total

    def disconnect(self, pin1: int, pin2: int) -> None:
        """
        Marks the given points as not connected and updates the data structures accordingly.

        :param pin1: The first pin
        :param pin2: The second pin
        """
        self.log.debug("Disconnecting pin %d and %d", pin1, pin2)
        find1 = self._ds.find(pin1)
        find2 = self._ds.find(pin2)

        self._not_connected[find1].add(find2)
        self._not_connected[find2].add(find1)

    def extract_networks(self) -> List[ElectricalNet]:
        """
        Returns a list containing all identified networks.
        """
        self.log.debug("Extracting electrical networks from pin connections")
        networks: List[ElectricalNet] = []
        self.log.debug("Num. networks: %d", len(list(self._ds.itersets())))
        for pin_set in self._ds.itersets():
            # Ensure that networks are only generated for sets of
            # two or more pins
            if len(pin_set) < 2:
                self.log.debug("Skipping pin set with only 1 pin")
                continue

            # Create a new network and
            network = ElectricalNet()
            for pin in pin_set:
                pin.network = network
            self.log.debug("Created network with %d pins: %s",
                           len(pin_set), pin_set)
            networks.append(network)

        return tuple(networks)

    def __repr__(self) -> str:
        return f"ConnectionManager[ds: {self._ds}, not_connected: {self._not_connected}]"
