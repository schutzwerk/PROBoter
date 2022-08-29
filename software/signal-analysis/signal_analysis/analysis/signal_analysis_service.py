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

import logging
from typing import Iterable

from signal_analysis.importer import CsvImporter
from signal_analysis.model import MeasurementSignal, AnalysedSignal, SignalGroup

from .pattern_analysis import PatternAnalysis
from .voltage_histogram import VoltageHistogram
from .event_interval_analysis import EventIntervalAnalysis
from .signal_group_aggregator import SignalGroupAggregator
from .protocol_identifier import ProtocolIdentifier


class SignalAnalysisService:
    """
    Service that provides various algorithms to analyze voltage signal
    measurement data
    """

    log = logging.getLogger(__name__)

    @classmethod
    def analyze_csv_data(cls, csv_data: str, filename: str = None) -> Iterable[SignalGroup]:
        """
        Identify the signal propertiies stored in a single CSV file

        :param csv_data: Raw file content of the CSV file to parse
        :type csv_data: str
        :param filename: Name of the original CSV file, defaults to None
        :type filename: str, optional
        :return: Analysis results
        :rtype: Iterable[SignalGroup]
        """
        # Import the measurement data
        signal_data = CsvImporter.import_csv_data(csv_data, filename)

        # Analyze the data
        return cls.analyze_measurement_data(signal_data)

    @classmethod
    def analyze_measurement_data(cls, signal_data: Iterable[MeasurementSignal])\
            -> Iterable[SignalGroup]:
        """
        Identify the functions and protocols from a list
        of voltage datasets
        """
        # Generate a list of signals with their properties
        cls.log.debug('Analyzing %d measurement signals', len(signal_data))
        analysis_results = cls.evaluate_signal_properties(signal_data)

        # Group related signals
        cls.log.info('Grouping signals...')
        signal_groups = SignalGroupAggregator.aggregate(analysis_results)

        # Perform protocol identification
        cls.log.info('Identifying protocols...')
        signal_groups = ProtocolIdentifier.identify_protocols(signal_groups)

        return signal_groups

    @classmethod
    def evaluate_signal_properties(cls, signal_data: Iterable[MeasurementSignal]) \
            -> Iterable[AnalysedSignal]:
        """
        Evaluates the properties for each entry in a list of signal data.
        The analysis is performed over several steps, each evaluating a
        different aspect of the signal

        :param signal_data: List of objects, which contain voltage data
                            from a measurement
        :type signal_data: Iterable[MeasurementSignal]
        :return: Collection of evaluated signals
        :rtype: Iterable[AnalysedSignal]
        """
        evaluated_signals = []
        for signal in signal_data:
            # Voltage properties
            cls.log.debug('Evaluating voltage properties of signal %d',
                          signal.index)
            voltage_histogram = VoltageHistogram(signal.voltage_data)

            # Interval evaluation
            cls.log.debug('Performing interval evaluation of signal %d',
                          signal.index)
            event_analysis = EventIntervalAnalysis(signal)
            event_properties = event_analysis.event_properties

            # Pattern analysis
            cls.log.debug('Performing pattern analysis of signal %d',
                          signal.index)
            pattern_results = PatternAnalysis.analyze(signal,
                                                      event_properties)

            # Create a new analysis result
            result = AnalysedSignal()
            result.signal = signal
            result.voltage_properties = voltage_histogram.voltage_level_properties
            result.event_properties = event_properties
            result.pattern_properties = pattern_results

            evaluated_signals.append(result)

        return evaluated_signals
