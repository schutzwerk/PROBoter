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

from abc import ABC
from enum import Enum
from typing import Tuple, List
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from proboter.model import ProbeType
from proboter.fields import NumpyArray


class CameraState(str, Enum):
    """
    Possible camera states
    """
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    STREAMING = "STREAMING"
    UNDEFINED = "UNDEFINED"


@dataclass
class CameraStatus:
    """
    Camera status
    """
    # Camera unique identifier
    id: int = -1
    # Displayable camera name
    name: str = ""
    # Camera index
    index: int = -1
    # Camera resolution as tuple of (width, height) in pixel
    resolution: Tuple[int, int] = None
    # Whether the camera hardware is connected
    connected: bool = False


class SignalMultiplexerChannelSwitchState(str, Enum):
    """
    Signal multiplexer channel states
    """
    DIGITAL = "D"
    ANALOG_A = "A"
    ANALOG_B = "B"
    NOT_CONNECTED = "N"


class SignalMultiplexerChannelDigitalLevel(str, Enum):
    """
    Signal multiplexer digitalized channel value
    """
    HIGH = "HIGH"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


@dataclass
class SignalMultiplexerStatus:
    """
    A signal multiplexer board's state
    """
    # The unique multiplexer identifier
    id: int = -1
    # Name of the current signal multiplexer configuration
    name: str = ""
    # Whether the signal multiplexer hardware is connected
    connected: bool = False
    # Channel switch states
    channel_switch_states: Tuple[SignalMultiplexerChannelSwitchState,
                                 SignalMultiplexerChannelSwitchState,
                                 SignalMultiplexerChannelSwitchState,
                                 SignalMultiplexerChannelSwitchState] = (
        SignalMultiplexerChannelSwitchState.NOT_CONNECTED,
        SignalMultiplexerChannelSwitchState.NOT_CONNECTED,
        SignalMultiplexerChannelSwitchState.NOT_CONNECTED,
        SignalMultiplexerChannelSwitchState.NOT_CONNECTED,
    )
    # Channel pull states
    channel_pull_states: Tuple[SignalMultiplexerChannelDigitalLevel,
                               SignalMultiplexerChannelDigitalLevel,
                               SignalMultiplexerChannelDigitalLevel,
                               SignalMultiplexerChannelDigitalLevel] = (
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
    )
    # Channel digital levels
    channel_digital_levels: Tuple[SignalMultiplexerChannelDigitalLevel,
                                  SignalMultiplexerChannelDigitalLevel,
                                  SignalMultiplexerChannelDigitalLevel,
                                  SignalMultiplexerChannelDigitalLevel] = (
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
        SignalMultiplexerChannelDigitalLevel.UNKNOWN,
    )


@dataclass
class UartInterfaceAdapterStatus:
    """
    UART interface adapter status
    """
    # Wether the UART interface adapter hardware is connected
    connected: bool = False
    # Whether the UART connection has been opened
    open: bool = False


@dataclass
class PicoscopeStatus:
    """
    A picoscope state
    """
    # Picoscope unique identifier
    id: int = -1
    # Whether the Picoscope hardware is connected
    connected: bool = False


@dataclass
class ProbeStatus:
    """
    A probe's status
    """
    # Probe unique identifier
    id: int = -1
    # Displayable probe name
    name: str = ""
    # Order-index used for collision detection and path planning
    order_index: int = -1
    # Probe type
    probe_type: ProbeType = ProbeType.P1
    # Whether the probe hardware is connected
    connected: bool = False
    # Whether the probe is moving
    moving: bool = False
    # The current probe position in the local probe coordinate system
    # (might not be accurate if status is 'MOVING')
    current_position_local: NumpyArray = Field(default_factory=lambda: np.zeros(3),
                                               np_shape=3)
    #
    # The current probe position in the global coordinate system
    # (might not be accurate if status is 'MOVING')
    current_position_global: NumpyArray = Field(default_factory=lambda: np.zeros(3),
                                                np_shape=3)


@ dataclass
class LightControllerStatus:
    """
    Light controller status
    """
    # Whether the light controller hardware is connected
    connected: bool = False
    # Whether the light is on
    on: bool = False


@ dataclass
class TargetPowerControllerStatus:
    """
    Target power controller status
    """
    # Whether the target power controller hardware is connected
    connected: bool = False
    # Whether the target is currently powered
    on: bool = False


@ dataclass
class ProboterStatus:
    """
    PROBoter status
    """
    id: int
    name: str
    probes: List[ProbeType]
    static_cameras: List[int]
    movable_cameras: List[int]
    has_light_controller: bool
    has_picoscope: bool
    has_signal_multiplexer: bool
    has_uart_adapter: bool
    has_target_power_controller: bool


class Event(ABC):
    """
    Base class for all events
    """


@ dataclass
class NewCameraFrameEvent(Event):
    """
    Event that indicates a new camera frame
    """
    # The camera that created the frame
    camera: 'Camera'
    # Unique identifier of the camera that created the frame
    camera_id: int
    # The camera frame raw data
    data: np.ndarray
    # Resolution
    resolution: Tuple[int, int]


@ dataclass
class CameraStatusChangedEvent(Event):
    """
    Event that indicates a change in a camera's status
    """
    # Unique identifier of the camera who's status has changed
    id: int
    # The new camera status
    status: CameraStatus


@ dataclass
class ProbeStatusChangedEvent(Event):
    """
    Event that indicates a change in a probe's status
    """
    # Unique identifier of the probe who's status has changed
    id: int
    # The new camera status
    status: ProbeStatus


@ dataclass
class ProbeMoveStartEvent(Event):
    """
    Event that indicates the start of a probe movement
    """
    # Probe that will move
    probe_type: ProbeType
    # Movement start (local coordinates)
    start_local: np.ndarray = np.zeros(3)
    # Movement start (global coordinates)
    start_global: np.ndarray = np.zeros(3)
    # Movement destination (local coordinates)
    destination_local: np.ndarray = np.zeros(3)
    # Movement destination (global coordinates)
    destination_global: np.ndarray = np.zeros(3)
    # Movement feed in mm/min
    feed: float = 1000


@ dataclass
class ProbeMoveFinishEvent(Event):
    """
    Event that indicates the end of a prove movement
    """
    # Probe that has moved
    probe_type: ProbeType


@ dataclass
class LightControllerChangedEvent(Event):
    """
    Event that indicates a change in light controller status
    """
    # The new light controller status
    status: LightControllerStatus


@ dataclass
class TargetPowerControllerChangedEvent(Event):
    """
    Event that indicates a change in the power state
    """
    # The new target power controller status
    status: TargetPowerControllerStatus


@ dataclass
class UartDataReceivedEvent(Event):
    """
    Event that indicates that new data via a UART interface have been received
    """
    # Received data as UTF-8 encoded string
    data: str
