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
from dataclasses import dataclass, field
from typing import Tuple, Iterable, Dict, Callable, Iterator, List, Optional

import numpy as np

from proboter.model import ProbeType

from .probe import Probe


# Alias
Position = np.ndarray
Constraint = Callable[[Position, Position], bool]


# Exceptions
class InvalidDestinationsError(Exception):
    """
    Exception used to express an error in the destinations
    determined for moving probes.
    """


# Utilities
def is_between(value: Position,
               left: Optional[float] = None, right: Optional[float] = None) -> bool:
    """
    Checks whether point is between the given left and right boundaries

    If left is None, it is replaced by negative infinity.
    The same is done for right with positive infinity.

    :param value: The point to check
    :param left: The left boundary or None for negative infinity
    :param right: The right boundary or None for positive infinity
    :return: Whether value is between left and right
    """
    bigger_than_left = left is None or left <= value[0]
    smaller_than_right = right is None or value[0] < right
    return bigger_than_left and smaller_than_right


@dataclass
class ProbeMovement:
    """
    Probe movement definition
    """
    # Probe to move
    probe: Probe
    # Movement destination in the common reference system
    destination: np.ndarray = field(default_factory=lambda: np.zeros(3))
    # Movement feed in mm / min
    feed: float = 1000


class MoveCoordinator:
    """
    Class offering utility functions to plan movements.
    Validates destinations and coordinates collision free movement
    """

    log = logging.getLogger(__module__)

    def __init__(self, probes: Tuple[Probe], plane_speed: float = 3000,
                 drop_speed: float = 2000, soft_drop_speed: float = 300,
                 soft_drop_offset: float = 1):

        self.probes = sorted(
            probes, key=lambda probe: probe.probe_type.to_order_index())
        self._soft_drop_speed = soft_drop_speed
        self._soft_drop_offset = soft_drop_offset
        self._plane_feed = plane_speed
        self._drop_speed = drop_speed

        # Extract the individual probes for easier access
        probe_dict = {probe.probe_type: probe for probe in probes}
        self.probe_1 = probe_dict[ProbeType.P1] \
            if ProbeType.P1 in probe_dict else None
        self.probe_11 = probe_dict[ProbeType.P11] \
            if ProbeType.P11 in probe_dict else None
        self.probe_2 = probe_dict[ProbeType.P2] \
            if ProbeType.P2 in probe_dict else None
        self.probe_21 = probe_dict[ProbeType.P21] \
            if ProbeType.P21 in probe_dict else None

        # Initially determine the highest common Z level
        # This may vary from probe to probe due to assembly / manufacturing
        # errors
        tmp_point = np.zeros(3)
        self._safe_z_height_high_2 = max(probe.map_local_to_global_point(tmp_point)[2]
                                         for probe in probes)
        self._safe_z_height_high_1 = self._safe_z_height_high_2 + 5
        self._safe_z_height_low = self._safe_z_height_high_1 + 3
        self.log.debug("Using safety Z levels %.3f, %.3f, %.3f",
                       self._safe_z_height_high_1,
                       self._safe_z_height_high_2,
                       self._safe_z_height_low)

        # Create a default set of collision avoidance rules
        self.constraints = self._make_constraints()

    def validate_destinations(
            self, probe_point_map: Dict[Probe, Position]) -> None:
        """
        Checks whether the probe point pairings violate any constraints

        :param probe_point_map: A dictionary mapping probes to their destinations
        :raise InvalidDestinationsError: If the set of probes is not continuous or
                                         any of the defined movement constraints
                                         is violated
        """
        if not self._is_continuous(probe_point_map):
            raise InvalidDestinationsError(
                "Assigned set of probes should be continuous")

        # Probes sorted by x-axis
        probes = probe_point_map.keys()
        probes = sorted(
            probes, key=lambda probe: probe.probe_type.to_order_index())

        # Check if each sequential pair of probes for respective constraints
        for i, probe1 in enumerate(probes):
            dest1 = probe_point_map[probe1]
            for probe2 in probes[i + 1:]:
                dest2 = probe_point_map[probe2]
                constraints = self.constraints[(probe1, probe2)] \
                    if (probe1, probe2) in self.constraints else ()
                if not all(constraint(dest1, dest2)
                           for constraint in constraints):
                    raise InvalidDestinationsError(
                        f"Destinations violate constraints: "
                        f"{probe1.id:d} -> {dest1}, {probe2.id:d} -> {dest2}")

    def coordinate_movement(self, probe_point_map: Dict[Probe, Position],
                            soft_drop: bool = True) -> Iterator[List[ProbeMovement]]:
        """
        Returns an iterable of movements which can be executed in parallel

        The following movements are executed in order:
        1. Raising in z
        2. Moving in xy plane
        3. Lowering in z

        :param probe_point_map: A dictionary assign destinations to probes
        :return: An iterator providing lists of probe - destination pairs. Each
                 list represents set of movements which can be executed in parallel.
        :raise InvalidDestinationsError: If the set of probes is not continuous or
                                         any of the defined movement constraints
                                         is violated
        """
        self.log.debug("Start probe movement coordination:")
        for probe, dest in probe_point_map.items():
            self.log.debug("%s: %s", probe.probe_type, dest)

        # Check if the movement is valid and does not result in a crash
        self.validate_destinations(probe_point_map)

        # Move all unused probes to their respective safety positions
        self._add_destinations_for_remaining_probes(probe_point_map)

        # Perform an additional collision check
        start_positions = self._fetch_current_proboter_pose()
        # Collision pairs ordered from left to right!
        collision_pairs = ((self.probe_21, self.probe_2),
                           (self.probe_2, self.probe_1),
                           (self.probe_1, self.probe_11))
        xy_feed_map = {probe: self._plane_feed for probe in self.probes}

        while True:
            intersection_detected = False

            for collision_pair in collision_pairs:
                # Check if we have a path intersection
                left_probe = collision_pair[0]
                right_probe = collision_pair[1]
                intersection = self._calculate_x_intersection(source_1=start_positions[left_probe],
                                                              destination_1=probe_point_map[left_probe],
                                                              feed_1=xy_feed_map[left_probe],
                                                              source_2=start_positions[right_probe],
                                                              destination_2=probe_point_map[right_probe],
                                                              feed_2=xy_feed_map[right_probe])
                # If we have a potential collision the feed is reduced for both probes
                # to the slowest one to avoid a collision
                if intersection is not None:
                    self.log.debug("Intersection %s <-> %s: %s",
                                   left_probe.probe_type, right_probe.probe_type, intersection)
                    self.log.debug("Reducing probe speed")
                    xy_feed_map[left_probe] = intersection[1]
                    xy_feed_map[right_probe] = intersection[2]

                    # If we had an intersection in one of the pairs, we need to redo the
                    # calculation for all the other pairs
                    intersection_detected = True

            if not intersection_detected:
                break

        # Phase 1: raise z-axis
        yield from self._raise_z_axis()

        # Phase 2: move in x,y plane
        yield from self._move_in_xy_plane(probe_point_map, xy_feed_map)

        # Phase 3: move to final positions (lower z-axis)
        yield from self._lower_z_axis(probe_point_map, soft_drop)

    def _fetch_current_proboter_pose(self) -> Dict[Probe, np.ndarray]:
        proboter_pose = {}
        for probe in self.probes:
            proboter_pose[probe] = probe.position_global
        return proboter_pose

    @classmethod
    def _calculate_x_intersection(cls, source_1: np.ndarray,
                                  destination_1: np.ndarray,
                                  feed_1: float,
                                  source_2: np.ndarray,
                                  destination_2: np.ndarray,
                                  feed_2: float) -> Optional[Tuple[float, float, float]]:

        x_min_1 = min(source_1[0], destination_1[0])
        x_max_1 = max(source_1[0], destination_1[0])

        # Intersection pre-check
        could_intersect = x_min_1 <= source_2[0] <= x_max_1 \
            or x_min_1 <= destination_2[0] <= x_max_1
        if not could_intersect:
            return None

        # Check for a real intersection
        dir_1 = destination_1 - source_1
        dist_1 = np.sqrt(np.sum(np.square(dir_1)))
        dir_1 /= dist_1
        dir_2 = destination_2 - source_2
        dist_2 = np.sqrt(np.sum(np.square(dir_2)))
        dir_2 /= dist_2

        # Calculate the speed in x-direction in mm/s
        vx_1 = feed_1 / 60 * dir_1[0]
        vx_2 = feed_2 / 60 * dir_2[0]
        # Calculate the differential speed between the two probes in mm/s
        vx_diff = vx_1 - vx_2

        # If at least one probe does not move in the x direction, the crash should have been
        # detected before. This has to be done to avoid division by zero.
        if abs(vx_1) == 0 or abs(vx_2) == 0:
            return None

        if abs(vx_diff) < 1e-7:
            # No intersection in time because the velocity
            # difference is too small
            return None

        # Calculate the time it would take for the two probes to drive the difference in
        # x-direction between their staring positions with their differential speed.
        t_travel = (source_2[0] - source_1[0]) / vx_diff

        # Calculate if the time for a collision is smaller than the actual travel time in
        # x-direction for the two probes. We check the lower limit against 0.1 to account for
        # rounding errors which may lead to crashes
        if -0.1 <= t_travel <= dist_1 / (feed_1 / 60) \
                and -0.1 <= t_travel <= dist_2 / (feed_2 / 60):
            # If yes, we need to reduce the travel time
            min_vx = min((abs(vx_1), abs(vx_2)))
            feed_1_adjusted = feed_1 * min_vx / abs(vx_1)
            feed_2_adjusted = feed_2 * min_vx / abs(vx_2)

            # Further decrement the speed of the slower probe to create a buffer zone and avoid
            # close contact (reduce by 10%)
            if feed_1_adjusted < feed_2_adjusted:
                feed_1_adjusted -= feed_1_adjusted * 0.2
            else:
                feed_2_adjusted -= feed_2_adjusted * 0.2

            return t_travel, feed_1_adjusted, feed_2_adjusted

        return None

    def _make_constraints(
            self) -> Dict[Tuple[Probe, Probe], Iterable[Constraint]]:
        """
        Defines the default constraints for safe probe positions.
        The constraints include:
            Any two probes not being able to pass each other on the x-axis
            Probes 1.1 and 1 to keep a sufficient z distance or a sufficient y distance
            Probes 2.1 and 2 to keep a sufficient z distance or a sufficient y distance

        : return: A dictionary mapping any two probes two a collection of
                 constraints applying to their positions. The constraints are
                 provided as functions taking the respective probe positions,
                 and returning true or false depending on the validity of the
                 positions.
        """
        constraints = {}
        n_probes = len(self.probes)
        for i in range(n_probes - 1):
            probe_1 = self.probes[i]
            for j in range(i + 1, n_probes):
                probe_2 = self.probes[j]
                constraints[(probe_1, probe_2)] = [lambda point_1,
                                                   point_2: point_1[0] <= point_2[0]]

        return constraints

    def _is_continuous(self, probe_point_map: Dict[Probe, Position]) -> bool:
        """
        Checks whether the points which ar to be probed are assigned to a
        continuous set of probes(e.g. Probes[1, 2, 2.1] vs[1.1, 2, 2.1])

        : param probe_point_map: A dictionary mapping probes to their destinations.
        : return: True if the probes building the key set of the dictionary are
                 a continuous subset of all probes
        """
        self.log.debug("Checking probe assignment of probes")
        self.log.debug("%s", [probe.probe_type.value for probe in self.probes])
        started = False
        stopped = False
        for probe in self.probes:
            is_there = probe in probe_point_map and probe_point_map[probe] is not None
            if stopped and is_there:
                self.log.warning("Probe %s is not continuous",
                                 probe.probe_type)
                return False

            if is_there:
                self.log.debug("Probe %s is the first probe to be moved",
                               probe.probe_type)
                started = True
            if started and not is_there:
                self.log.debug("Probe %s is the last probe",
                               probe.probe_type)
                stopped = True
        return True

    def _add_destinations_for_remaining_probes(self,
                                               probe_point_map: Dict[Probe, Position]) -> None:
        """
        Finds and assigns safe positions to the remaining probes

        Probes left of the left-most probe in the probe_point_map are assigned
        to position left of the left-most destination. Same is done for probes
        right of the right-most probe being assigned positions right of the
        right-most destination.

        : param probe_point_map: A dictionary assign destinations to probes
        : type: probe_point_map: Dict[Probe, Position]
        """
        destinations = probe_point_map.values()
        x_positions = [destination[0] for destination in destinations]
        min_x = min(x_positions)
        max_x = max(x_positions)
        probe_count_diff = len(self.probes) - len(probe_point_map)
        delta = 20
        x = min_x - probe_count_diff * delta
        for probe in self.probes:
            if probe in probe_point_map:
                break
            if probe.position_global[0] < x:
                x = probe.position_global[0]
            z_level = self._safe_z_height_low
            if probe.probe_type == ProbeType.P1:
                z_level = self._safe_z_height_high_1
            if probe.probe_type == ProbeType.P2:
                z_level = self._safe_z_height_high_2
            probe_point_map[probe] = np.array(
                [x, probe.position_global[1], z_level])
            x += delta

        x = max_x + probe_count_diff * delta
        for probe in reversed(self.probes):
            if probe in probe_point_map:
                break
            if probe.position_global[0] > x:
                x = probe.position_global[0]
            z_level = self._safe_z_height_low
            if probe.probe_type == ProbeType.P1:
                z_level = self._safe_z_height_high_1
            if probe.probe_type == ProbeType.P2:
                z_level = self._safe_z_height_high_2
            probe_point_map[probe] = np.array(
                [x, probe.position_global[1], z_level])
            x -= delta

    def _raise_z_axis(self) -> Iterator[List[ProbeMovement]]:
        """
        Sequentially coordinates raising probes in the z-axis

        First, the two inner probes 1 and 2 are raised in parallel. Then,
        the two outer probes 1.1 and 2.1 are raised together.

        : return: An iterator providing lists of probe - destination pairs. Each
                 list represents set of movements which can be executed in parallel.
        """
        self.log.debug("Clearing probes in z direction")
        inner_probes = (self.probe_1, self.probe_2)
        outer_probes = (self.probe_11, self.probe_21)

        # Raise all probes to their safety positions
        movements = []
        for inner_probe in inner_probes:
            pos = inner_probe.position_global
            pos[2] = self._safe_z_height_high_1 \
                if inner_probe.probe_type == ProbeType.P1 \
                else self._safe_z_height_high_2
            movements.append(ProbeMovement(probe=inner_probe,
                                           destination=pos,
                                           feed=self._drop_speed))
        for outer_probe in outer_probes:
            pos = outer_probe.position_global
            pos[2] = self._safe_z_height_low
            movements.append(ProbeMovement(probe=outer_probe,
                                           destination=pos,
                                           feed=self._drop_speed))
        yield movements

    def _move_in_xy_plane(self, probe_point_map: Dict[Probe, Position],
                          feed_map: Dict[Probe, float]) \
            -> Iterator[List[ProbeMovement]]:
        """
        Move each probe in the xy axis plane at the same time.

        : param probe_point_map: A dictionary assign destinations to probes
        : return: An iterator providing lists of probe - destination pairs.
                 Each list represents set of movements which can be executed in
                 parallel.
        """
        self.log.debug("Positioning probes in the XY plane")
        inner_probes = (self.probe_1, self.probe_2)
        outer_probes = (self.probe_11, self.probe_21)
        movements = []
        for probe in inner_probes:
            dest = np.copy(probe_point_map[probe])
            dest[2] = self._safe_z_height_high_1 \
                if probe.probe_type == ProbeType.P1 \
                else self._safe_z_height_high_2
            movements.append(ProbeMovement(probe=probe,
                                           destination=dest,
                                           feed=feed_map[probe]))
        for probe in outer_probes:
            dest = np.copy(probe_point_map[probe])
            dest[2] = self._safe_z_height_low
            movements.append(ProbeMovement(probe=probe,
                                           destination=dest,
                                           feed=feed_map[probe]))
        yield movements

    def _lower_z_axis(self, probe_point_map: Dict[Probe, Position],
                      soft_drop: bool = True) -> Iterator[List[ProbeMovement]]:
        """
        Sequentially coordinates lowering probes in the z-axis

        First, the two outer probes 1.1 and 2.1 are lowered in parallel. Then,
        the two inner probes 1 and 2 are lowered together.

        : return: An iterator providing lists of probe - destination pairs. Each
                 list represents set of movements which can be executed in parallel.
        """
        self.log.debug("Lowering probes in z direction")
        # TODO: We have an issue here, when soft drop is enabled but not all probes are used. In
        #  this case the unused probes are first driven upwards by 'soft_drop_offset' because
        #  their position is subtracted with 'soft_dopt_offset' and afterwards a soft drop is
        #  executed. This comes, because the move coordinator cannot differentiate between used
        #  and unused probes.

        if soft_drop:
            # Lower with default speed to the soft drop offset in Z
            high_speed_drop_movements = []
            for probe, pos in probe_point_map.items():
                # TODO Handle cases where the probe destination is so high
                #      that the drop_offset would be above the safe Z level!!
                drop_pos = pos - np.array((0, 0, self._soft_drop_offset))
                high_speed_drop_movements.append(ProbeMovement(probe=probe,
                                                               destination=drop_pos,
                                                               feed=self._drop_speed))
            self.log.debug("Lowering to soft drop offset")
            yield high_speed_drop_movements

        # Lower to the final destination
        movements = []
        feed = self._soft_drop_speed if soft_drop else self._drop_speed
        for probe, pos in probe_point_map.items():
            movements.append(ProbeMovement(probe=probe,
                                           destination=pos,
                                           feed=feed))
        self.log.debug("Lowering to final position")
        yield movements
