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

from typing import Iterable, Any

import numpy as np
from pydantic.json import ENCODERS_BY_TYPE

ENCODERS_BY_TYPE[np.ndarray] = lambda v: v.tolist()


class NumpyArray(np.ndarray):
    """
    Numpy array field
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema, field):
        shape = field.field_info.extra.get("np_shape", 1)

        field_schema["type"] = "array"

        if isinstance(shape, int):
            # 1D vector
            field_schema["items"] = {
                "type": "number",
                "minItems": shape,
                "maxItems": shape
            }
        elif isinstance(shape, Iterable):
            # Multi-dimensional array
            #
            # Reverse the order of the dimensions as the field
            # definition goes from inside out
            rev_shape = list(shape)
            rev_shape.reverse()

            field = {
                "type": "number",
                "minItems": rev_shape[0] if rev_shape[0] > 0 else None,
                "maxItems": rev_shape[0] if rev_shape[0] > 0 else None
            }

            for dim in rev_shape[1:]:
                field = {
                    "type": "array",
                    "items": field,
                    "minItems": dim if dim > 0 else None,
                    "maxItems": dim if dim > 0 else None
                }
            field_schema["items"] = field

        else:
            raise ValueError(f"Invalid shape type: {type(shape)}")

        field_schema["example"] = np.zeros(shape).tolist()

    @ classmethod
    def validate(cls, value: Any) -> np.ndarray:
        """
        Validate / convert a given value into a numpy array

        :param value: Value to convert
        :type value: Any
        :return: Converted value as numpy array 
        :rtype: np.ndarray
        """
        # TODO Add input type checks here!
        return np.asarray(value)
