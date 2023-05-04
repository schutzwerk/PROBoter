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

from .task import Task
from .task_processor import TaskProcessor

from .calibrate_probe_task import CalibrateProbeTask, \
    CalibrateProbeTaskParameter, CalibrateProbeTaskResult

from .calibrate_static_camera_task import CalibrateStaticCameraTask, \
    CalibrateStaticCameraParameter, CalibrateStaticCameraResult

from .calibrate_camera_intrinsics_task import CalibrateCameraIntrinsicsTask, \
    CalibrateCameraIntrinsicsParameter, CalibrateCameraIntrinsicsResult

from .scan_pcb_static_camera_task import ScanPcbStaticCameraTask, \
    ScanPcbStaticCameraParameter, ScanPcbStaticCameraResult

from .probe_uart_task import UartProbingMoveTask, UartProbingMoveTaskParameter, \
    UartProbingMoveTaskResult

from .probe_electrical_connectivity_task import ProbeElectricalConnectivityTask, \
    ProbeElectricalConnectivityParameter, ProbeElectricalConnectivityResult

from .measure_voltage_signals_task import MeasureVoltageSignalsTask, \
    MeasureVoltageSignalsParameter, MeasureVoltageSignalsResult

from .move_proboter_task import MoveProboterTask, MoveProboterParameter, \
    MoveProboterResult

from .demo_mode_task import ProbePartyTask, ProbePartyParameter, ProbePartyResult
