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

import csv


class CsvExporter:
    """
    CSV exporter for grouped signals
    """

    @classmethod
    def export_signalgroup(cls, filename, time_resolution_in_ns,
                           grouped_data):
        with open(filename, 'w', newline='', encoding='utf-8') as output_csvfile:
            sample_data_writer = csv.writer(
                output_csvfile,
                delimiter=',',
                quotechar='|'
            )
            # Creating header for CSV-file
            row_for_csv = []
            row_for_csv.append(time_resolution_in_ns)
            sample_data_writer.writerow(row_for_csv)

            # Adding data for CSV-file
            for dataline in grouped_data:
                row_for_csv = []
                for data in dataline:
                    row_for_csv.append(data)
                sample_data_writer.writerow(row_for_csv)
                del row_for_csv
        return True
