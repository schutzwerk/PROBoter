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

import math
import datetime
from typing import Iterable

from signal_analysis.exporter import CsvExporter as csvexport
from signal_analysis.exporter import PulseviewExporter as plsvexport

from .signal_analysis_result import AnalysedSignal


class SignalGroup:
    """
    List of aggregated signals follows always the same scheme:
        [0]: Clock (empty list if not available)
        [1]: Data1
        [2]: Data2 (if available)
        [3]: Control (not yet implemented)
    """

    def __init__(self, analyzed_signals: Iterable[AnalysedSignal]):
        self.analyzed_signals: Iterable[AnalysedSignal] = analyzed_signals
        self.protocol_name: str = None
        self.identification_ratings = None
        self.encoding_parameters = {}
        self.correlation_rating: float = -1

    @property
    def clock_signal(self) -> AnalysedSignal:
        """
        Return the clock signal if any, otherwise None
        """
        return self.analyzed_signals[0] if len(self.analyzed_signals) >= 1 else None

    @property
    def data1_signal(self) -> AnalysedSignal:
        """
        Return the first data signal if any, otherwise None
        """
        return self.analyzed_signals[1] if len(self.analyzed_signals) >= 2 else None

    @property
    def data2_signal(self) -> AnalysedSignal:
        """
        Return the second data signal if any, otherwise None
        """
        return self.analyzed_signals[2] if len(self.analyzed_signals) >= 3 else None

    @property
    def control_signal(self) -> AnalysedSignal:
        """
        Return the control signal if any, otherwise None
        """
        return self.analyzed_signals[3] if len(self.analyzed_signals) >= 4 else None

    def export_csv(self):
        # Maybe, a deepcopy might be required, if the del instruction at
        # the end of this function does also remove
        # all the underlying objects
        signals_for_export = self.analyzed_signals.copy()
        if signals_for_export[0] == []:
            signals_for_export = signals_for_export[1:]
        self.__rebase(signals_for_export)
        time_resolution = signals_for_export[0].get_time_resolution()
        grouped_signals = self.__get_export_data(signals_for_export)
        filename = self.__generate_filename(grouped_signals[0])
        filename = filename + ".csv"
        print(f"Generating file: {filename}")
        if csvexport.export_signalgroup(filename,
                                        time_resolution,
                                        grouped_signals):
            print(f"Export of {self.protocol_name} successful")
        del signals_for_export

    def export_pulseview(self):
        signals_for_export = self.analyzed_signals.copy()
        if signals_for_export[0] == []:
            signals_for_export = signals_for_export[1:]
        self.__rebase(signals_for_export)
        time_resolution = signals_for_export[0].get_time_resolution()
        grouped_signals = self.__get_export_data(signals_for_export)
        filename = self.__generate_filename(grouped_signals[0])
        filename = filename + ".sr"
        print(f"Generating filename: {filename}")
        is_digital_data = (self.__is_binary_voltage_levels())

        if is_digital_data:
            if plsvexport.export_digital_data_to_sigrok(filename,
                                                        time_resolution,
                                                        grouped_signals):
                print(f"Export of {self.protocol_name} successful")
        elif not is_digital_data:
            if plsvexport.export_analog_data_to_sigrok(filename,
                                                       time_resolution,
                                                       grouped_signals):
                print(f"Export of {self.protocol_name} successful")
        print("pulseview-exporter started")

    def print_signal_basic_information(self):
        print("")
        print("New signal:")
        print(
            f"Amount of contained signals: {len(self.analyzed_signals)}")
        for signal in self.analyzed_signals:
            if signal != []:
                print(f"  Signal type: {signal.signal_type}")
            else:
                print("Line in signal group not defined")

    def to_json(self):
        return {
            "protocol_name": self.protocol_name,
            "signals": {
                "clock": self.clock_signal.signal.index if self.clock_signal else None,
                "data1": self.data1_signal.signal.index if self.data1_signal else None,
                "data2": self.data2_signal.signal.index if self.data2_signal else None,
                "control": self.control_signal.signal.index if self.control_signal else None,
            },
            "identification_ratings": self.identification_ratings,
            "encoding_parameters": self.encoding_parameters,
            "correlation_rating": self.correlation_rating
        }

    @staticmethod
    def __get_new_optimum_resolution(signals):
        list_of_resolutions = []
        for signal in signals:
            if signal != []:
                resolution = signal.get_time_resolution()
                list_of_resolutions.append(resolution)
        gcd = list_of_resolutions[0]
        for resolution in list_of_resolutions:
            gcd = math.gcd(gcd, resolution)
        print(f"GCD of resolution: {gcd}")
        return gcd

    @staticmethod
    def __get_max_required_duration_ns(signals):
        list_of_durations = []
        for signal in signals:
            if signal != []:
                duration = signal.get_measurement_duration()
                list_of_durations.append(duration)
                print(f"Required duration: {duration}")
        return max(list_of_durations)

    def __rebase(self, signals_for_export):
        resolution = self.__get_new_optimum_resolution(signals_for_export)
        duration = self.__get_max_required_duration_ns(signals_for_export)
        for signal in signals_for_export:
            if signal != []:
                signal.rebase_time(resolution, duration)

    @staticmethod
    def __get_export_data(signals):
        """
        Gathers the data for exporting, consisting of one array
        (one entry for each time), which contains several data for the
        respective time
        """
        data_to_export = []
        dataline = []
        # dataline.append("Time signal")
        for signal in signals:
            dataline.append("Line_" + str(signal.get_index()))
        data_to_export.append(dataline)
        del dataline

        for i in range(signals[0].get_voltage_array_length()):
            dataline = []
            # Time signal will not be exported and
            # was therefore removed from export functionality:
            # time_signal = time_resolution * i
            # dataline.append(time_signal)
            for signal in signals:
                datum = signal.get_voltage_data(i)
                dataline.append(datum)
            data_to_export.append(dataline)
            del dataline
        return data_to_export

    def __generate_filename(self, signals_index_list):
        signal_name = ""
        for name in signals_index_list:
            signal_name = signal_name + "__" + str(name)
        now = datetime.datetime.now()
        datestring = now.strftime("_%Y-%m-%d_%H%M%S")
        indexlist = "_index"
        for signal in self.analyzed_signals:
            if signal != []:
                indexlist = indexlist + "_" + str(signal.get_index())
        filename = "meas_data/" + self.protocol_name + \
            signal_name + indexlist + datestring
        return filename

    def __is_binary_voltage_levels(self):
        for signal_line in self.analyzed_signals:
            if signal_line != []:
                if signal_line.number_of_voltage_levels != 2:
                    return False
        return True

    def __repr__(self) -> str:
        return ("SignalGroup: "
                f"num_aggregated_signals = {len(self.analyzed_signals)}, "
                f"protocol_name = {self.protocol_name}, "
                f"identification_ratings = {self.identification_ratings}, "
                f"encoding_parameters = {self.encoding_parameters}, "
                f"correlation_rating = {self.correlation_rating}")
