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

from typing import Iterable
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt


class MeasurementSignal:
    """
    Voltage signal measurement for a single input channel
    """

    def __init__(self, index: int, source_name: str, voltage_levels: Iterable[float],
                 measurement_resolution: float, start_time: datetime):
        self.__index = index
        self.__source_name = source_name
        self.__voltage_levels = voltage_levels
        self.__time_resolution_ns = measurement_resolution
        self.__start_time = start_time

    @property
    def index(self) -> int:
        return self.__index

    @property
    def source_name(self) -> str:
        return self.__source_name

    @property
    def start_time(self) -> datetime:
        return self.__start_time

    @property
    def time_resolution(self) -> float:
        return self.__time_resolution_ns

    @property
    def measurement_duration(self) -> float:
        return len(self.__voltage_levels) * self.__time_resolution_ns

    @property
    def voltage_array_length(self) -> int:
        return len(self.__voltage_levels)

    @property
    def voltage_data(self):
        return tuple(self.__voltage_levels)

    @property
    def voltage_standard_deviation(self) -> float:
        return np.std(self.voltage_data)

    @property
    def voltage_mean(self) -> float:
        return np.mean(self.voltage_data)

    def rebase_time(self, new_time_resolution, new_duration):
        if (new_time_resolution != self.__time_resolution_ns) \
                or (new_duration != len(self.__voltage_levels) * self.__time_resolution_ns):
            new_voltage_array = \
                [None] * (int(new_duration / new_time_resolution))
            rebasing_factor_for_index = \
                int(new_time_resolution / self.time_resolution)
            print(f"Rebasing factor for index is: {rebasing_factor_for_index}")
            for i, voltage_level in self.__voltage_levels:
                new_voltage_array[rebasing_factor_for_index * i] = \
                    voltage_level
            self.__time_resolution_ns = new_time_resolution
            self.__voltage_levels = new_voltage_array

    def plot_signal_index(self):
        data_array = self.__voltage_levels
        index_array = range(len(data_array))
        plt.figure()
        plt.title('Plot of Signal')
        plt.plot(index_array, data_array)
        plt.xlabel('Index')
        plt.ylabel('Voltage signal /mV')
        plt.legend()
        plt.show(block=False)

    def __repr__(self) -> str:
        return ("MeasurementSignal: "
                f"index={self.index}, "
                f"source={self.source_name}, "
                f"resolution={self.time_resolution:E}, "
                f"data points={self.voltage_array_length}")
