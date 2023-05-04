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

import numpy as np
from pydantic import Field

from proboter.fields import NumpyArray
from proboter.hardware import Probe, Proboter
from proboter.model import ReferenceBoardConfig

from .task import Task
from .utils import LinearAlgebra, CircleFit, ReferenceBoard
from .exceptions import ProbeCalibrationException


@dataclass
class CalibrateProbeTaskParameter:
    """
    Probe calibration task parameter
    """
    # ID of the reference board to use
    reference_board: int
    # Number of calibration runs to perform
    num_calibration_runs: int = 1
    # The feed used during calibration in mm/mini
    calibration_feed: float = 1000
    # Whether to home the unit before each calibration run
    home_before_calibration: bool = True
    # The initial probing positions as (4x3) numpy array
    initial_probe_positions: NumpyArray = Field(default_factory=lambda: np.zeros(4, 3),
                                                np_shape=(4, 3))


@dataclass
class CalibrateProbeTaskResult:
    """
    Result of a probe calibration run
    """
    # Unique identifier of the calibrated probe
    probe: int
    # (4x4) transformation matrix form the probe's local
    # coordinate system to the global system
    tmat_local_to_global: NumpyArray = Field(default_factory=lambda: np.eye(4),
                                             np_shape=(4, 4))
    # (4x4) transformation matrix from the global system
    # to the probe's local system
    tmat_global_to_local: NumpyArray = Field(default_factory=lambda: np.eye(4),
                                             np_shape=(4, 4))
    # Residuals from the mapping of the measured local pin centers
    # to the reference coordinates of the reference board as (8x3) numpy array
    residuals_local_to_global: NumpyArray = Field(
        default_factory=lambda: np.zeros(8, 3),
        np_shape=(8, 3))
    # Residuals from the mapping of the reference coordinates to the
    # measured local pin centers as (8x3) numpy array
    residuals_global_to_local: NumpyArray = Field(
        default_factory=lambda: np.array((8, 3)),
        np_shape=(8, 3))
    # Max. residuals from the mapping of the measured local pin centers
    # to the reference coordinates of the reference board as 3D numpy vector
    max_residuals_local_to_global: NumpyArray = Field(
        default_factory=lambda: np.zeros(3),
        np_shape=3)
    # Positions of the ideal reference pin locations of the reference board
    # as (8x3) numpy array
    ref_pin_centers: NumpyArray = Field(
        default_factory=lambda: np.array((8, 3)),
        np_shape=(8, 3))
    # Measured / circle-fitted reference pin locations as (8x3) numpy array
    measured_ref_pin_centers: NumpyArray = Field(
        default_factory=lambda: np.array((8, 3)),
        np_shape=(8, 3))


class CalibrateProbeTask(
        Task[CalibrateProbeTaskParameter, CalibrateProbeTaskResult]):
    """
    Task to calibrate a single electrical probe
    """

    log = logging.getLogger(__name__)

    def __init__(self, params: CalibrateProbeTaskParameter,
                 probe: Probe,
                 proboter: Proboter,
                 reference_board_config: ReferenceBoardConfig):
        """
        Initialize a new probe calibration task
        """
        super().__init__("CalibrateProbe", params)
        self._probe = probe
        self._proboter = proboter
        self._reference_board = ReferenceBoard(reference_board_config)

    async def run(self) -> CalibrateProbeTaskResult:
        """
        Calculate the transformation matrix from the probe to the global coordinate
        system defined by a reference board. To achieve this, 4 points of each reference
        pin are probed and the reference pin center is subsequently calculated with
        a circle fit algorithm.

        When positioned at each probing start position, the probe must touch one
        of the reference pins when lowering the z axis. Otherwise the probe can be
        damaged or even get destroyed!

        : return: Calibration results
        : rtype: ProbeCalibrationResult
        """
        # Move all other probe to their respective safety positions
        # await self._proboter.clear_area_for_probe(self._probe)

        # Switch the probe's channel to the analogue output
        multiplexer = self._proboter.signal_multiplexer
        probe_channel = multiplexer.get_channel_by_probe(self._probe)
        await multiplexer.connect_to_analog(probe_channel)
        self.log.info("Switched multiplexer channel %s to analogue output",
                      probe_channel)

        if self.params.home_before_calibration:
            # Home axes
            await self._proboter.home_probe(self._probe)

        local_inner_pins = []
        num_probing_points = self.params.initial_probe_positions.shape[0]
        for i in range(num_probing_points):
            # Probe a single point
            probing_pos = self.params.initial_probe_positions[i, :]
            # SAFETY FIX - Always set probing Z to avoid crashs during initial
            # positioning
            probing_pos[2] = 0.0
            self.log.info("Probing point %d of %d at (%.3f, %.3f, %.3f)",
                          i + 1, num_probing_points, probing_pos[0],
                          probing_pos[1], probing_pos[2])
            pos, radius, error = await self._probe_single_point(probe=self._probe,
                                                                probing_pos=probing_pos,
                                                                feed=self.params.calibration_feed)
            local_inner_pins.append((pos, radius, error))

        # Sort the reference points (largest radius first)
        local_inner_pins.sort(key=lambda rp: rp[1], reverse=True)

        self.log.info("Successfully probed all 4 inner pins: %s",
                      local_inner_pins)
        min_z = min(p[0][2] for p in local_inner_pins)
        max_z = max(p[0][2] for p in local_inner_pins)
        self.log.info("Ref. pin plane z (min, max, max diff.): %.4f, %.4f, %.4f",
                      min_z, max_z, abs(max_z - min_z))

        self.log.info("Estimating transformation matrix "
                      "from innter ref. pins")
        tmp_x = (local_inner_pins[3][0] - local_inner_pins[0][0]) \
            / self._reference_board.width  # D10 -> D7
        tmp_y = (local_inner_pins[0][0] - local_inner_pins[2][0]) \
            / self._reference_board.height  # D8 -> D10
        tmp_z = np.cross(tmp_x, tmp_y)
        tmp_z /= np.sqrt(np.sum(np.square(tmp_z)))
        tmp_origin = local_inner_pins[0][0].copy()  # D10
        tmp_origin += 0.5 * self._reference_board.width * tmp_x
        tmp_origin -= 0.5 * self._reference_board.height * tmp_y

        tmat_inner_global_to_local = np.eye(4)
        tmat_inner_global_to_local[0:3, 0] = tmp_x
        tmat_inner_global_to_local[0:3, 1] = tmp_y
        tmat_inner_global_to_local[0:3, 2] = tmp_z
        tmat_inner_global_to_local[0:3, 3] = tmp_origin

        local_inner_pin_centers = np.zeros((4, 3))
        for i in range(4):
            local_inner_pin_centers[i, :] = np.array(local_inner_pins[i][0])
        self.log.info(("Successfully calculated the global to probe local "
                       "system transformation: %s"),
                      tmat_inner_global_to_local)

        # Extended calibration
        global_outer_pin_centers = self._reference_board.ext_reference_pin_coordinates
        self.log.debug("Probing raised brass pin centers at ref. coordinates: %s",
                       global_outer_pin_centers)
        local_outer_pin_centers = np.zeros((4, 3), dtype=np.float32)
        for i in range(4):
            local_outer_pin = np.matmul(tmat_inner_global_to_local,
                                        np.array([global_outer_pin_centers[i, 0],
                                                  global_outer_pin_centers[i, 1],
                                                  global_outer_pin_centers[i, 2],
                                                  1]))[0:3]
            local_outer_pin[2] = 0.0
            self.log.info("Probing ext. point %d of %d at (%.3f, %.3f, %.3f)",
                          i + 1, 4, local_outer_pin[0],
                          local_outer_pin[1], local_outer_pin[2])
            pos, _, error = await self._probe_single_point(probe=self._probe,
                                                           probing_pos=local_outer_pin,
                                                           feed=self.params.calibration_feed)
            local_outer_pin_centers[i, :] = np.array(pos)
        self.log.debug("Successfully probed raised brass pins at: %s",
                       local_outer_pin_centers)

        # Refine the transformation matrix with the newly measured points
        global_inner_pin_centers = self._reference_board.reference_pin_coordinates
        tmat_global_to_local, residuals_global_to_local = LinearAlgebra.calculate_base_change(
            p_b1=np.concatenate(
                (global_inner_pin_centers, global_outer_pin_centers)),
            p_b2=np.concatenate((local_inner_pin_centers, local_outer_pin_centers)))

        max_abs_residuals = np.abs(residuals_global_to_local).max(axis=0)
        self.log.info("TMat ref. -> local max. residuals: %.2E, %.2E, %.2E",
                      max_abs_residuals[0], max_abs_residuals[1], max_abs_residuals[2])
        tmat_local_to_global, residuals_local_to_global = LinearAlgebra.calculate_base_change(
            p_b1=np.concatenate((local_inner_pin_centers,
                                 local_outer_pin_centers)),
            p_b2=np.concatenate((global_inner_pin_centers,
                                 global_outer_pin_centers)))

        max_abs_residuals = np.abs(residuals_local_to_global).max(axis=0)
        self.log.info("TMat local -> ref. max. residuals: %.2E, %.2E, %.2E",
                      max_abs_residuals[0], max_abs_residuals[1], max_abs_residuals[2])

        self.log.info("Successfully calculated the probe -> ref. transformation matrix: %s",
                      tmat_local_to_global)

        # Final validation
        tmp_ref_pins = np.ones((4, 4))
        tmp_ref_pins[:, 0:3] = local_inner_pin_centers
        calc_ref_pins = np.matmul(
            tmat_local_to_global, tmp_ref_pins.T).T[:, 0:3]

        # Finally, raise the z-axis
        p_end = np.zeros(3)
        await self._probe.move_to_local_position(p_end, self.params.calibration_feed)

        return CalibrateProbeTaskResult(probe=self._probe.id,
                                        tmat_local_to_global=tmat_local_to_global,
                                        tmat_global_to_local=tmat_global_to_local,
                                        ref_pin_centers=np.concatenate((local_inner_pin_centers,
                                                                        local_outer_pin_centers)),
                                        measured_ref_pin_centers=calc_ref_pins,
                                        residuals_local_to_global=residuals_local_to_global,
                                        residuals_global_to_local=residuals_global_to_local,
                                        max_residuals_local_to_global=max_abs_residuals)

    @classmethod
    async def _probe_single_point(cls, probe: Probe, probing_pos: np.ndarray, feed: float):
        """
        Probe a single reference pin on the reference board
        """
        # Move the probe to the current probing position
        await probe.move_to_local_position(probing_pos, feed=feed)

        # Probe 4 edge points of the reference pin
        try:
            pin_points = await probe.center_probe()
        except ProbeCalibrationException:
            error_msg = (f"Failed to probe reference point at ("
                         f"{probing_pos[0]:.3f}, "
                         f"{probing_pos[1]:.3f}, "
                         f"{probing_pos[2]:.3f})")
            cls.log.error(error_msg)
            raise ProbeCalibrationException(error_msg) from None

        x = pin_points[:, 0]
        y = pin_points[:, 1]
        z = pin_points[:, 2]
        z_mean = np.mean(z)

        # Circle fitting to get the reference pin center and radius
        circle_result = CircleFit.fit_least_squares(x, y)

        # Clear the z axis
        pos_z_cleared = probe.position
        pos_z_cleared[2] = 0.0
        await probe.move_to_local_position(position=pos_z_cleared,
                                           feed=feed)

        return np.array((circle_result.center[0], circle_result.center[1], z_mean)), \
            circle_result.radius, \
            circle_result.residuals
