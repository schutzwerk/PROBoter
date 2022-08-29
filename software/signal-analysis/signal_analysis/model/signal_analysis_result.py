# Copyright (C) 2022  SCHUTZWERK GmbH
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

from enum import Enum
from typing import Iterable
from dataclasses import dataclass

from .measurement_signal import MeasurementSignal


class SignalType(Enum):
    """
    Enumeration of defined voltage signal types
    """
    PERIODIC = 'PERIODIC'
    BURST = 'BURST'
    SPORADIC = 'SPORADIC'
    GROUND = 'GROUND'
    CONST_VOLTAGE = 'CONST_VOLTAGE'
    UNKNOWN = 'UNKNOWN'


@dataclass
class VoltageLevelProperties:
    """
    Voltage level analysis result
    """
    number_of_voltage_levels: int = -1
    relative_width_of_upper_voltage_level: int = -1
    relative_width_of_lowest_voltage_level: int = -1
    main_voltage_levels: Iterable[float] = ()


@dataclass
class EventIntervalProperties:
    """
    Voltage signal event interval analysis result
    """
    interval_array: Iterable[float] = ()
    signed_interval_array: Iterable[float] = ()
    transmission_activity_list: Iterable[float] = ()
    amount_reoccuring_durations: int = None
    amount_of_events: int = None
    amount_of_event_pairs: int = None
    longest_activity: int = None
    event_duration_symmetry: int = False
    first_reoccuring_duration: int = None
    double_event_duration: int = None
    time_first_activity: float = None
    time_last_activity: float = None
    transmission_block_duration: int = None
    timelist_of_incidents: Iterable[int] = None
    voltage_of_longest_duration: float = None
    are_state_durations_int_multiple: bool = False
    signal_type: SignalType = SignalType.UNKNOWN


@dataclass
class PatternProperties:
    """
    Voltage signal pattern analysis result
    """
    repeating_pattern_duration_symbols: float = None
    repeating_pattern_duration_ns: int = None


@dataclass
class AnalysedSignal:
    """
    An analyzed voltage signal
    """
    # The voltage measurement signal the analysis results belong to
    signal: MeasurementSignal = None
    # Results of the voltage level analysis
    voltage_properties: VoltageLevelProperties = None
    # Results of the event interval analysis
    event_properties: EventIntervalProperties = None
    # Results of the pattern analysis
    pattern_properties: PatternProperties = None
