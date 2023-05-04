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

from io import BytesIO
from typing import Union, Iterable

import cv2
import numpy as np
from flask import make_response, send_file, Response
from flask_restx import fields, Api, Namespace, Model


from project_storage.middleware import ComponentService, NetworkService, \
    PinService, PcbService, ScanService


def get_scan_service() -> ScanService:
    """
    Return current scan service
    """
    return ScanService()


def get_pcb_service() -> PcbService:
    """
    Return the current PCB service
    """
    return PcbService()


def get_network_service() -> NetworkService:
    """
    Return the current Network service
    """
    return NetworkService()


def get_pin_service() -> PinService:
    """
    Return the current Pin service
    """
    return PinService()


def get_component_service() -> ComponentService:
    """
    Return the current Component service
    """
    return ComponentService()


class NullableString(fields.String):
    """
    Nullable string field
    """
    __schema_type__ = ['string', 'null']
    __schema_example__ = 'nullable string'


class NullableInteger(fields.Integer):
    """
    Nullable integer field
    """
    __schema_type__ = ['integer', 'null']
    __schema_example__ = 'nullable integer'


def array_field(shape: Union[int, Iterable[int]],
                **kwargs) -> fields.List:
    """
    Generate a Flask RESTx field representing a fixed
    size multi-dimensional array

    :param shape: Shape of the fixed-size array. Can be a scalar value or an
                  iterable list of integers.
    :type shape: Union[int, Iterable[int]]
    :param attribute: Optional attribute value as described in the flask_restx
                      documentation, defaults to None
    :type attribute: Optional[Union[str, Callable]]
    :return: Flask RESTx model field defining the array
    :rtype: fields.List
    """
    if isinstance(shape, int):
        # Single dimension
        field = fields.List(fields.Float,
                            **kwargs)
        if shape > 0:
            field.min_items = shape
            field.max_items = shape
        return field

    if isinstance(shape, Iterable):
        # Multi-dimensional arrayfrom flask_restx import Api,

        # Reverse the order of the dimensions as the field
        # definition goes from inside out
        rev_shape = list(shape)
        rev_shape.reverse()

        field = fields.List(fields.Float,
                            min_items=rev_shape[0] if rev_shape[0] > 0 else None,
                            max_items=rev_shape[0] if rev_shape[0] > 0 else None)
        for idx, dim in enumerate(rev_shape[1:]):
            if idx + 1 == len(rev_shape) - 1:
                # Set the attributes only on the last list field
                field = fields.List(field,
                                    min_items=dim if dim > 0 else None,
                                    max_items=dim if dim > 0 else None,
                                    **kwargs)
            else:
                field = fields.List(field,
                                    min_items=dim if dim > 0 else None,
                                    max_items=dim if dim > 0 else None)

        return field

    raise ValueError(f"Invalid shape type: {type(shape)}")


def error_model(api: Union[Api, Namespace]) -> Model:
    """
    Default error model consisting of a dictionary
    containing only the key 'message' describing the
    error cause

    :param api: The API instance to use (required for proper Swagger documentation)
    :type api: Union[Api, Namespace]
    :return: The API model
    :rtype: Model
    """
    return api.model('Error', {
        'message': fields.String
    })


def send_image(img: np.ndarray, filename: str = 'result.png') -> Response:
    """
    Send an image to a web client

    :param img: Image to send
    :type img: np.ndarray
    :param filename: Filename that should be sent to the client,
                     defaults to 'result.png'
    :type filename: str, optional
    :return: Response to send to the client
    :rtype: Response
    """
    # Convert the image to an encoded byte stream
    _, encoded_img = cv2.imencode('.png', img)
    img_io = BytesIO()
    img_io.write(encoded_img)
    img_io.seek(0)

    # Send the image
    response = make_response(send_file(img_io,
                                       mimetype='image/png',
                                       download_name=filename))
    response.headers['Cache-Control'] = 'no-cache'
    return response
