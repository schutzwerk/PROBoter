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

import os
import csv
import time
import logging
from typing import Iterable
from datetime import datetime

from signal_analysis.model.measurement_signal import MeasurementSignal


class CsvImporter:
    """
    Utility class to import voltage signal messages from a CSV file
    """

    log = logging.getLogger(__name__)

    @classmethod
    def import_csv_data(cls, data: str, filename: str = None,
                        start_time: datetime = None) -> Iterable[MeasurementSignal]:
        """
        Create a CsvImporter instance from the raw content of a CSV file

        :param data: CSV data
        :type data: str
        :param filename: Optional name of the file the data belongs to
        :type filename: str, optional
        :return: Iterable list of imported measurement signals
        :rtype: Iterable[MeasurementSignal]
        """
        cls.log.debug('Parsing CSV data of file \'%s\'',
                      filename if filename is not None else 'UNKNOWN')

        # Split the data into lines
        csv_lines = data.split('\n')
        # Remove empty lines and whitespace
        csv_lines = [line.strip()
                     for line in csv_lines
                     if line.strip() != '']

        # Interpret all lines as CSV data
        csv_reader = csv.reader(csv_lines, delimiter=',')

        # The first line contains the time resolution in nanoseconds
        resolution = int(float(next(csv_reader)[0]))

        # The second line contains the data input signal names
        name_list = [str(val) for val in next(csv_reader)]

        # Creating empty 2D array "list_of_voltage_signals"
        lst_of_voltage_signals = [[] for _ in name_list]
        # Parse the measurement data lines
        for row in csv_reader:
            for i, val in enumerate(row):
                # Reuse the last value if for the current signal line
                # no value is specified
                val = val if val != '' else lst_of_voltage_signals[i][-1]
                lst_of_voltage_signals[i].append(float(val))

        cls.log.debug('Successfully imported CSV data')

        # Convert the data to measurement signals
        measurement_signals = []
        for i, name in enumerate(name_list):
            source_name = filename if filename is not None else ""
            source_name += "/" + name
            signal = MeasurementSignal(index=i,
                                       source_name=source_name,
                                       voltage_levels=lst_of_voltage_signals[i],
                                       measurement_resolution=resolution,
                                       start_time=start_time)

            measurement_signals.append(signal)

        return measurement_signals

    @classmethod
    def from_file(cls, filename: str) -> Iterable[MeasurementSignal]:
        """
        Create a CsvImporter instance from a CSV file

        :param filename: Path to the file to import
        :type filename: str
        :return: Iterable list of imported measurement signals
        :rtype: Iterable[MeasurementSignal]
        """
        cls.log.debug('Reading CVS data from file \'%s\'', filename)
        with open(filename, encoding="utf8") as csv_file:
            csv_data = csv_file.read()

        return cls.import_csv_data(csv_data, filename, time.gmtime(os.path.getmtime(filename)))
