# Copyright (C) 2022 SCHUTZWERK GmbH
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

from flask import current_app
from flask_restx import Namespace, Resource, fields

from pcb_analysis.visual_analysis import AnalysisService


# Endpoint description
api = Namespace('detectors',
                path='/detectors',
                description='Information about available detectors')


# Models
chip_detector_model = api.model('ChipDetector', {
    'id': fields.String(example='fbb400c8-cbc4-4e11-b75a-ac788b239c95'),
    'name': fields.String(example='Faster R-CNN')
})

pin_detector_model = api.model('PinDetector', {
    'id': fields.String(example='fbb400c8-cbc4-4e11-b75a-ac788b239c95'),
    'name': fields.String(example='CV pipeline')
})


@api.route('/chip')
class ChipDetectorList(Resource):
    """
    Resource that provides information about availalbe chip detectors
    """
    @staticmethod
    @api.marshal_with(chip_detector_model, as_list=True)
    def get():
        """
        Return a list of available chip detectors
        """
        analysis_service: AnalysisService = current_app.analysis_service
        return list(analysis_service.chip_detectors)


@api.route('/pin')
class PinDetectorList(Resource):
    """
    Resource that provides information about available pin detectors
    """
    @staticmethod
    @api.marshal_with(pin_detector_model, as_list=True)
    def get():
        """
        Return a list of available pin detectors
        """
        analysis_service: AnalysisService = current_app.analysis_service
        return list(analysis_service.pin_detectors)
