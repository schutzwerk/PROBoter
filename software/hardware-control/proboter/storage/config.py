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

import aiohttp


class StorageBackendConfig:
    """
    Storage backend configuration and utility functions
    """
    # Storage service base URL
    BASE_URL = "http://localhost:5000/api/v1"

    log = logging.getLogger(__module__)

    @classmethod
    def session(cls) -> aiohttp.ClientSession:
        """
        Create a default session to connect to the
        storage service backend

        :rtype: aiohttp.ClientSession
        """
        return aiohttp.ClientSession()

    @classmethod
    def api_url(cls, path: str) -> str:
        """
        Build the full storage URL for a given
        relative API endpoint URL

        :param path: Relative API endpoint URL
        :type path: str
        :return: Full API URL
        :rtype: str
        """
        cls.log.info("Storage backend URL: %s", cls.BASE_URL)
        return cls.BASE_URL + path
