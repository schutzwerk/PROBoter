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

from tortoise import fields

from .entity import Entity


class AxesControllerConfig(Entity):
    """
    Configuration of a single axes controller
    """
    # pylint: disable=too-few-public-methods
    # The axes controller ID
    id: int = fields.IntField(pk=True)
    # USB device to use
    usb_device_name: str = fields.CharField(100, null=False)
    # The baud rate used for the communication via the
    # serial console
    baud_rate: int = fields.IntField(null=False)
    # The board UUID
    uuid: str = fields.CharField(36, null=False)
    # Whether the controller board is a light controller
    is_light_controller: bool = fields.BooleanField(null=False, default=False)
