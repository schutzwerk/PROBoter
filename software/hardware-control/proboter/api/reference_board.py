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

import logging
from typing import List
from dataclasses import dataclass

from quart import Blueprint
from quart_schema import validate_response, validate_request, tag

from proboter.model import ReferenceBoardConfig

from .utils import ApiTags, ApiException, ApiErrorResponse, ApiSuccessResponse


log = logging.getLogger(__name__)

bp = Blueprint('reference-board', __name__, url_prefix="/reference-board")


# Accepted here to reduce the amount of requests to fetch all information
# regarding a single reference board
# pylint: disable=too-many-instance-attributes
@dataclass
class ReferenceBoardRequest:
    """
    Reference board creation or update request
    """
    name: str
    inner_brass_pin_width: float
    inner_brass_pin_height: float
    raised_brass_pin_width: float
    raised_brass_pin_height: float
    thickness: float
    marker_width: float
    marker_height: float
    marker_grid_width: float
    marker_grid_height: float
    outer_white_pin_width: float
    outer_white_pin_height: float
    outer_brass_pin_width: float
    outer_brass_pin_height: float

    def update_config(self, config: ReferenceBoardConfig) -> None:
        """
        Update a given reference board config with the values of this request

        :param config: Reference board configuration to update
        :type config: ReferenceBoardConfig
        """
        config.name = self.name
        config.inner_brass_pin_width = self.inner_brass_pin_width
        config.inner_brass_pin_height = self.inner_brass_pin_height
        config.raised_brass_pin_width = self.raised_brass_pin_width
        config.raised_brass_pin_height = self.raised_brass_pin_height
        config.thickness = self.thickness
        config.marker_width = self.marker_width
        config.marker_height = self.marker_height
        config.marker_grid_width = self.marker_grid_width
        config.marker_grid_height = self.marker_grid_height
        config.outer_white_pin_width = self.outer_white_pin_width
        config.outer_white_pin_height = self.outer_white_pin_height
        config.outer_brass_pin_width = self.outer_brass_pin_width
        config.outer_brass_pin_height = self.outer_brass_pin_height

    def to_config(self) -> ReferenceBoardConfig:
        """
        Convert the request into a new reference board config instance

        :return: The newly created reference board configuration
        :rtype: ReferenceBoardConfig
        """
        config = ReferenceBoardConfig()
        self.update_config(config)
        return config


@ dataclass
class ReferenceBoardResponse(ReferenceBoardRequest):
    """
    Reference board response
    """
    id: int

    @ staticmethod
    def from_config(config: ReferenceBoardConfig) -> "ReferenceBoardResponse":
        """
        Create an API response from a given reference board configuration
        :rtype: ReferenceBoardResponse
        """
        return ReferenceBoardResponse(id=config.id,
                                      name=config.name,
                                      inner_brass_pin_width=config.inner_brass_pin_width,
                                      inner_brass_pin_height=config.inner_brass_pin_height,
                                      raised_brass_pin_width=config.raised_brass_pin_width,
                                      raised_brass_pin_height=config.raised_brass_pin_height,
                                      thickness=config.thickness,
                                      marker_width=config.marker_width,
                                      marker_height=config.marker_height,
                                      marker_grid_width=config.marker_grid_width,
                                      marker_grid_height=config.marker_grid_height,
                                      outer_white_pin_width=config.outer_white_pin_width,
                                      outer_white_pin_height=config.outer_white_pin_height,
                                      outer_brass_pin_width=config.outer_brass_pin_width,
                                      outer_brass_pin_height=config.outer_brass_pin_height)


@dataclass
class ReferenceBoardListResponse:
    """
    Reference board list response
    """
    reference_boards: List[ReferenceBoardResponse]


@ bp.route('', methods=["GET"])
@ validate_response(ReferenceBoardListResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.REFERENCE_BOARD])
async def get_all_reference_boards() -> ReferenceBoardListResponse:
    """
    Return a list all defined reference boards
    """
    log.info("Reference board request for all stored boards received")
    reference_boards = [ReferenceBoardResponse.from_config(config)
                            async for config in ReferenceBoardConfig.all()]
    return ReferenceBoardListResponse(reference_boards)


@ bp.route('', methods=["POST"])
@ validate_request(ReferenceBoardRequest)
@ validate_response(ReferenceBoardResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.REFERENCE_BOARD])
async def create_reference_board(data: ReferenceBoardRequest) -> ReferenceBoardResponse:
    """
    Create a new reference board
    """
    log.info("New reference board request received")
    config = data.to_config()
    await config.save()
    return ReferenceBoardResponse.from_config(config)


@ bp.route('/<int:reference_board_id>', methods=["GET"])
@ validate_response(ReferenceBoardResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.REFERENCE_BOARD])
async def get_reference_board(reference_board_id: int) -> ReferenceBoardResponse:
    """
    Return a reference board
    """
    log.info("Reference board request for ID %d received",
             reference_board_id)
    config = await ReferenceBoardConfig.get_by_id(reference_board_id)
    if config is None:
        raise ApiException("Reference board not found")
    return ReferenceBoardResponse.from_config(config)


@ bp.route('/<int:reference_board_id>', methods=["PUT"])
@ validate_request(ReferenceBoardRequest)
@ validate_response(ReferenceBoardResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.REFERENCE_BOARD])
async def update_reference_board(reference_board_id: int,
                                 data: ReferenceBoardRequest) -> ReferenceBoardResponse:
    """
    Update a reference board
    """
    log.info("Reference board update request for ID %d received",
             reference_board_id)
    config = await ReferenceBoardConfig.get_by_id(reference_board_id)
    if config is None:
        raise ApiException("Reference board not found")
    data.update_config(config)
    await config.save()
    return ReferenceBoardResponse.from_config(config)


@ bp.route('/<int:reference_board_id>', methods=["DELETE"])
@validate_response(ApiSuccessResponse, 200)
@ validate_response(ApiErrorResponse, 500)
@ tag([ApiTags.REFERENCE_BOARD])
async def delete_reference_board(reference_board_id: int) -> ApiSuccessResponse:
    """
    Update a reference board
    """
    log.info("Reference board delete request for ID %d received",
             reference_board_id)
    await ReferenceBoardConfig.delete_by_id(reference_board_id)
    return ApiSuccessResponse(), 200
