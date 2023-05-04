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

import json

import numpy as np
from sqlalchemy import types
from flask_sqlalchemy import SQLAlchemy


# pylint: disable=too-many-ancestors
class NumpyArrayStringType(types.TypeDecorator):
    """
    Stores numpy arrays as JSON serialized unicode strings
    """
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        # Allow nullable / empty fields
        if value is None:
            return value
        assert isinstance(value, np.ndarray), 'value must be a numpy array'
        return json.dumps(value.tolist())

    def process_result_value(self, value, dialect):
        # Allow nullable / empty fields
        if value is None:
            return value
        return np.array(json.loads(value))

    def copy(self, **kw):
        return NumpyArrayStringType(self.impl.length)

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()

    @property
    def python_type(self):
        return np.ndarray


# pylint: disable=too-many-ancestors
class NumpyArrayUInt8Type(types.TypeDecorator):
    """
    Stores integer numpy arrays as binary data
    """
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
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
        return size_header + value.tobytes()

    def process_result_value(self, value, dialect):
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

    def copy(self, **kw):
        return NumpyArrayUInt8Type(self.impl.length)

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()

    @property
    def python_type(self):
        return np.ndarray


# pylint: disable=too-many-ancestors
class NumpyArrayFloat32Type(types.TypeDecorator):
    """
    Stores 32bit float numpy arrays as binary data
    """
    impl = types.LargeBinary

    def process_bind_param(self, value, dialect):
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
        return size_header + value.tobytes()

    def process_result_value(self, value, dialect):
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

    def copy(self, **kw):
        return NumpyArrayFloat32Type(self.impl.length)

    def process_literal_param(self, value, dialect):
        raise NotImplementedError()

    @property
    def python_type(self):
        return np.ndarray


# The global SQLAlchemy instance
db = SQLAlchemy()
