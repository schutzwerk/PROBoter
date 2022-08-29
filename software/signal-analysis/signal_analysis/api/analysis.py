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

from flask import current_app, request, abort
from werkzeug.datastructures import FileStorage
from flask_restx import Namespace, Resource, fields

from signal_analysis.model import MeasurementSignal
from signal_analysis.analysis import SignalAnalysisService
from signal_analysis.importer import CsvImporter


log = logging.getLogger(__name__)

# Endpoint description
api = Namespace('analysis',
                path='/analysis',
                description='Voltage signal analysis operations')

# Models
voltage_signal_model = api.model('voltage-signal', {
    'index': fields.Integer(required=True),
    'source_name': fields.String(required=True, example='Picoscope'),
    'voltage_levels': fields.List(fields.Float, required=True,
                                  example=[-1.5, 1.0, 5.2]),
    'measurement_resolution': fields.Integer(required=True, example=40),
    'start_time': fields.DateTime(default=None)
})

identification_rating_model = api.model('identification-ratings', {
    'I2C': fields.Float,
    'SPI': fields.Float,
    'UART': fields.Float,
    'OneWire': fields.Float,
})

protocol_analysis_result_model = api.model('protocol-analysis-result', {
    'protocolName': fields.String(attribute='protocol_name',
                                  example='I2C'),
    'signals': fields.Nested(api.model('signal-model', {
        'clock': fields.Integer(attribute='clock'),
        'data1': fields.Integer(attribute='data1'),
        'data2': fields.Integer(attribute='data2'),
        'control': fields.Integer(attribute='control')
    }),
        attribute='signals'),
    'identificationRatings': fields.Nested(identification_rating_model,
                                           attribute='identification_ratings'),
    'encodingParameters': fields.Raw(attribute='encoding_parameters'),
    'correlationRating': fields.Float(attribute='correlation_rating'),
})

# Request parser
input_parser = api.parser()
input_parser.add_argument(
    'voltage-datasets',
    dest='voltage_datasets',
    type=FileStorage,
    location='files',
    help="Voltage CSV-datasets for analysis",
    # "action=append"-incompatibility. Patch swagger.py:
    # https://github.com/python-restx/flask-restx/issues/177
    action='append')


@api.route('')
class VoltageAnalysisResource(Resource):
    """
    Resource that exposes voltage signal analysis functionality
    """
    @staticmethod
    @api.expect([voltage_signal_model])
    @api.marshal_with(protocol_analysis_result_model, as_list=True)
    def post():
        """
        Analyse measurement data in JSON format
        """
        log.info("JSON analysis request from %s", request.remote_addr)

        request_data = request.json
        # Check for single measurement input
        if isinstance(request_data, dict):
            request_data = [request_data, ]

        # Convert the JSON data to measurement data objects
        signals = []
        for raw_data in request_data:
            signal = MeasurementSignal(index=raw_data['index'],
                                       source_name=raw_data['source_name'],
                                       voltage_levels=raw_data['voltage_levels'],
                                       measurement_resolution=raw_data['measurement_resolution'],
                                       start_time=raw_data['start_time'])
            signals.append(signal)

        analysis_service: SignalAnalysisService = current_app.analysis_service
        signal_groups = analysis_service.analyze_measurement_data(signals)

        return [sig.to_json() for sig in signal_groups]


@api.route('/file')
class VoltageAnalysisFileResource(Resource):
    """
    Resource that allows analysis of voltage record data files like CSV files
    """
    @staticmethod
    @api.expect(input_parser)
    @api.response(400, 'Invalid input data')
    @api.marshal_with(protocol_analysis_result_model, as_list=True)
    def post():
        """
        Analyse a file containing voltage signal measurement data
        """
        log.info("Analysis request from %s", request.remote_addr)

        analysis_service: SignalAnalysisService = current_app.analysis_service

        # Parse the request parameters
        args = input_parser.parse_args()

        if args.voltage_datasets is None:
            abort(400, 'Missing input file')

        signal_datasets = []  # Will contain the set of datasets measured / imported from CSV-file
        if all(voltage_dataset.mimetype == 'text/csv'
               for voltage_dataset in args['voltage_datasets']):
            for voltage_dataset in args['voltage_datasets']:
                raw_csv_dataset = voltage_dataset.read().decode('utf-8')
                filename = voltage_dataset.filename  # TODO: Substitute with read filename
                raw_binary_dataset = CsvImporter.import_csv_data(
                    raw_csv_dataset, filename)
                for raw_binary_data in raw_binary_dataset:
                    signal_datasets.append(raw_binary_data)
            signal_groups = analysis_service.analyze_measurement_data(
                signal_datasets)

        return [sig.to_json() for sig in signal_groups]
