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
import dataclasses
from typing import Any

import numpy as np


class EnhancedJsonEncoder(json.JSONEncoder):
    """
    JSON encoder that supports serialization of
    Python dataclasses and numpy.npdarrays
    """

    def default(self, o: Any) -> Any:
        """
        Convert a given data object into a JSON-serializable representation

        :param o: Object to convert
        :type o: Any
        :return: JSON-serializable representation of o
        :rtype: Any
        """
        if isinstance(o, np.ndarray):
            return o.tolist()
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return json.JSONEncoder.default(self, o)


def convert_to_camelcase(string: str) -> str:
    """
    Convert a string to camelCase by replacing underscore characters

    :param string: Input string
    :type string: str
    :return: Camel case string
    :rtype: str
    """
    return string.split('_')[0] + ''.join(x.capitalize() or '_'
                                          for x in string.split('_')[1:])


def convert_dict_to_camelcase(data: dict) -> dict:
    """
    Recursively convert keys in (nested) dictionaries to camelCase

    :param event_data: Dictionary to convert
    :type event_data: dict
    :return: The modified original dictionary
    :rtype: dict
    """
    if isinstance(data, dict):
        for key in tuple(data.keys()):
            new_key = convert_to_camelcase(key)

            # Recursively replace keys in nested dictionaries
            new_data = data.pop(key)
            if isinstance(new_data, dict):
                new_data = convert_dict_to_camelcase(new_data)

            # Finally store the value with the new key
            data[new_key] = new_data

    return data


def event_to_json(event: object) -> dict:
    """
    Convert a given event object into a JSON-serializable dictionary

    :param event: Event to serialize
    :type event: object
    :return: JSON-serializable representation of the event
    :rtype: dict
    """
    # Serialize the event into a dictionary
    typed_event = {
        "name": event.__class__.__name__,
        "data": event
    }
    serialized_event_dict = json.loads(json.dumps(typed_event,
                                                  cls=EnhancedJsonEncoder))

    # Convert the keys to camelCase
    event_dict = convert_dict_to_camelcase(serialized_event_dict)

    # Serialize the dictionary into a JSON string
    return json.dumps(event_dict)
