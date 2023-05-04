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

from datetime import datetime
from typing import Iterable, List, Type, Optional

import schema
import numpy as np


def to_datetime(format_string: str) -> object:
    """
    Return a schema validation object to convert a string
    into a datetime object according to a provided format string

    :param format_string: Datetime format string
    :type str: str
    :return: Schema validation object
    :rtype: object
    """
    return schema.And(str,
                      schema.Use(lambda dt_str: datetime.strptime(dt_str, format_string)))


def to_np_array(shape: List[int], dtype: Optional[Type]) -> object:
    """
    Return a schema validation object to convert a
    (nested) list into a numpy array with an expected
    shape

    :param shape: Expected array shape
    :type shape: Iterable[int]
    :param dtype: Numpy array data type. If set to None, Numpys
                  auto data type detection is used.
    :type dtype: Optional[Type]
    :return: Created schema validation object that can be used like
             any of the operators (e.g. And, Or) from the schema package
    :rtype: object
    """
    return schema.And(list,
                      lambda l: __np_shape_checker(l, shape),
                      schema.Use(lambda v: np.array(v, dtype=dtype)
                                 if dtype is not None else np.array(v)))


def __np_shape_checker(input_list: Iterable,
                       expected_shape: List[int]) -> bool:
    """
    Compare if the shape of a nested list matches an
    expected one

    First, the provided nested list is converted to a numpy array.
    The shape of the resulting array is then compared to the expected one.

    :param input_list: (Nested) list whose shape should be checked
    :type input_list: Iterable
    :param expected_shape: Expected shape of the (nested) list
    :type expected_shape: Iterable[int]
    :return: Whether the shape of the input list matches the expected shape
             (True) or not (False)
    :rtype: bool
    """
    shape = np.array(input_list).shape
    if len(shape) != len(expected_shape):
        return False

    for i, actual_dim in enumerate(shape):
        if expected_shape[i] < 0:
            continue
        if actual_dim != expected_shape[i]:
            return False
    return True
