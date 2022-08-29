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
import sys

from .csv_exporter import CsvExporter


class PulseviewExporter:
    """
    Pulseview data exporter
    """

    @classmethod
    def convert_mv_to_v(cls, grouped_signals):
        for i in range(1, len(grouped_signals)):
            data_at_same_time = grouped_signals[i]
            for j in range(1, len(data_at_same_time)):
                print(f"data entry pre division: {grouped_signals[i][j]}")
                grouped_signals[i][j] = grouped_signals[i][j]/1000
                print(f"data entry post division: {grouped_signals[i][j]}")
        return grouped_signals

    @classmethod
    def export_analog_data_to_sigrok(cls, filename,
                                     time_resolution_in_ns,
                                     grouped_data):
        grouped_data = cls.convert_mv_to_v(grouped_data)
        # Create CSV-file, which can then be converted to the sr-file
        csv_filename = os.path.splitext(filename)[-2]
        csv_filename = csv_filename + ".csv"
        print("Split filename", csv_filename)
        CsvExporter.export_signalgroup(
            filename,
            time_resolution_in_ns,
            grouped_data)

        # Create sigrok-file from using the sigrokdecode-cli-function
        # Example command string for creating sr-files:
        # https://sigrok.org/wiki/File_format:Csv
        ###
        # sigrok-cli -i uart_counter_uart_count_19200_5n1.csv
        # -I csv:start_line=2:first_column=2:samplerate=20000
        # -o uart_counter_uart_count_19200_5n1.sr
        commandstring = "sigrok-cli -i " + csv_filename \
            + " -I csv:column_formats=a,a:start_line=2:samplerate=" \
            + str(int(round(1/(time_resolution_in_ns/1000000000), 0))) \
            + " -o "+filename
        print(commandstring)
        os.system(commandstring)

    @classmethod
    def find_max_2d_array(cls, mat):
        """
        Taken from
        https://www.geeksforgeeks.org/program-to-find-the-maximum-element-in-a-matrix/
        , code is contributed by Surendra_Gangwar
        """
        # Initializing max element as INT_MIN
        max_element = -sys.maxsize - 1

        # checking each element of matrix
        # if it is greater than max_element,
        # update maxElement
        for i, _ in enumerate(mat):
            for j, _ in enumerate(mat[i]):
                if mat[i][j] is not None:
                    if mat[i][j] > max_element:
                        max_element = mat[i][j]

        # finally return max_element
        return max_element

    @classmethod
    def binarise_data(cls, grouped_data):
        # Converting measured analog data to digital data
        data_slice = grouped_data[1:]
        # distinction_limit = max([max(data_array_1),max(data_array_2)])/2
        distinction_limit = cls.find_max_2d_array(data_slice) / 2

        for line_index, _ in enumerate(grouped_data[1:]):
            for item_index, __ in enumerate(grouped_data[line_index]):
                item = grouped_data[line_index][item_index]
                if item is not None:
                    if grouped_data[line_index][item_index] < distinction_limit:
                        grouped_data[line_index][item_index] = 0
                    elif item >= distinction_limit:
                        grouped_data[line_index][item_index] = 3267.716535433071
                        # Why-ever Sigrok does not
                        # accept any lower values
                elif item is None:
                    grouped_data[line_index] = grouped_data[line_index - 1]
                    break

    @classmethod
    def export_digital_data_to_sigrok(cls,
                                      filename,
                                      time_resolution,
                                      grouped_data):

        # Create CSV-file, which can then be converted to the sr-file
        csv_filename = os.path.splitext(filename)[-2]
        csv_filename = csv_filename + ".csv"
        print("Split filename", csv_filename)
        # print(grouped_data)
        cls.binarise_data(grouped_data)
        CsvExporter.export_signalgroup(
            csv_filename,
            time_resolution,
            grouped_data)
        amount_of_signal_lines = len(grouped_data[2])
        columns_format = "l"
        for _ in range(amount_of_signal_lines - 1):
            columns_format = columns_format + ",l"

        # Create sigrok-file from using the sigrokdecode-cli-function

        # Example command string for creating sr-files:
        # sigrok-cli -i uart_counter_uart_count_19200_5n1.csv \
        # -I csv:start_line=2:first_column=2:samplerate=20000 \
        # -o uart_counter_uart_count_19200_5n1.sr
        command_string = "sigrok-cli -i "
        command_string += csv_filename
        command_string += " -I csv:column_formats="
        command_string += columns_format+":start_line=2:samplerate="
        command_string += str(int(round(1/(time_resolution/1000000000), 0)))
        command_string += " -o " + filename

        print(command_string)
        os.system(command_string)
        print("Export finished")
