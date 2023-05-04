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

import json
import logging
from typing import Optional

import numpy as np
from tortoise.fields import Field


class NumpyArrayStringField(Field[np.ndarray]):
    """
    Stores numpy arrays as JSON serialized strings
    """
    field_type = np.ndarray
    SQL_TYPE = "VARCHAR"

    log = logging.getLogger(__module__)

    def to_db_value(self, value: Optional[np.ndarray],
                    instance: "Union[Type[Model], Model]") -> Optional[str]:
        if value is None:
            return value
        assert isinstance(value, np.ndarray), 'value must be a numpy array'
        return json.dumps(value.tolist())

    def to_python_value(self, value: Optional[str]) -> Optional[np.ndarray]:
        # Allow nullable / empty fields
        if value is None or isinstance(value, self.field_type):
            return value
        return np.array(json.loads(value))


class NumpyArrayUInt8Field(Field[np.ndarray]):
    """
    Stores integer numpy arrays as binary data
    """
    field_type = np.ndarray
    SQL_TYPE = "BLOB"

    def to_db_value(self, value: Optional[np.ndarray],
                    instance: "Union[Type[Model], Model]") -> Optional[bytes]:
        # Allow nullable / empty fields
        if value is None:
            return value

        assert isinstance(value, np.ndarray), 'value must be a numpy array'
        assert value.dtype == np.uint8, 'dtype must be uin8'

        # Serialize the shape
        size_header = bytearray()
        # Number of dimensions
        size_header += len(value.shape).to_bytes(4, 'big')
        # Dimensions
        for dim in value.shape:
            size_header += dim.to_bytes(4, 'big')

        # Save the data + header information
        return bytes(size_header + value.tobytes())

    def to_python_value(self, value: Optional[bytes]) -> Optional[np.ndarray]:
        # Allow nullable / empty fields
        if value is None:
            return value

        # Restore the array shape information
        num_dims = int.from_bytes(value[:4], 'big')
        shape = []
        for i in range(num_dims):
            shape.append(int.from_bytes(value[(i + 1) * 4:(i + 2) * 4], 'big'))

        # Remove the header
        data = value[(num_dims + 1) * 4:]
        # Load the data and reshape
        data = np.frombuffer(data, np.uint8).reshape(shape)

        return data


class NumpyArrayFloat32Field(Field[np.ndarray]):
    """
    Stores 32bit float numpy arrays as binary data
    """
    field_type = np.ndarray
    SQL_TYPE = "BLOB"

    def to_db_value(self, value: Optional[np.ndarray],
                    instance: "Union[Type[Model], Model]") -> Optional[bytes]:
        # Allow nullable / empty fields
        if value is None:
            return value

        assert isinstance(value, np.ndarray), 'value must be a numpy array'
        assert value.dtype == np.float32, 'dtype must be float32'

        # Serialize the shape
        size_header = bytearray()
        # Number of dimensions
        size_header += len(value.shape).to_bytes(4, 'big')
        # Dimensions
        for dim in value.shape:
            size_header += dim.to_bytes(4, 'big')

        # Save the data + header information
        return bytes(size_header + value.tobytes())

    def to_python_value(self, value: Optional[bytes]) -> Optional[np.ndarray]:
        # Allow nullable / empty fields
        if value is None:
            return value

        # Restore the array shape information
        num_dims = int.from_bytes(value[:4], 'big')
        shape = []
        for i in range(num_dims):
            shape.append(int.from_bytes(value[(i + 1) * 4:(i + 2) * 4], 'big'))

        # Remove the header
        data = value[(num_dims + 1) * 4:]
        # Load the data and reshape
        data = np.frombuffer(data, np.float32).reshape(shape)

        return data
