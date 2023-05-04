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
from .probe_config import ProbeConfig
from .picoscope_config import PicoscopeConfig
from .signal_multiplexer_config import SignalMultiplexerConfig
from .uart_interface_adapter_config import UartInterfaceAdapterConfig
from .movable_camera_config import MovableCameraConfig
from .static_camera_config import StaticCameraConfig


class ProboterConfig(Entity):
    """
    Configuration of a single PROBoter hardware setup
    """
    # pylint: disable=too-few-public-methods
    # The PROBoter ID
    id: int = fields.IntField(pk=True)
    # Name of the PROBoter configuration
    name: str = fields.CharField(100, null=False)
    # Whether this PROBoter configuration is the active one
    is_active: bool = fields.BooleanField(null=False, default=False)
    # Probes belonging to the PROBoter config
    probes: fields.ReverseRelation[ProbeConfig]
    # Static cameras belonging to the PROBoter config
    static_cameras = fields.ReverseRelation[StaticCameraConfig]
    # Movable cameras belonging to the PROBoter config
    movable_cameras = fields.ReverseRelation[MovableCameraConfig]
    # Signal multiplexer configurations
    signal_multiplexer: fields.ReverseRelation[SignalMultiplexerConfig]
    # Picoscope configurations
    picoscope = fields.ReverseRelation[PicoscopeConfig]
    # UART interface adapter
    uart_interface_adapter: fields.ReverseRelation[UartInterfaceAdapterConfig]

    @ classmethod
    async def get_active_config(cls) -> "ProboterConfig":
        """
            Fetch the current / active PROBoter configuration

            :return: The current / active PROBoter configuration or None if no
                     such configuration is defined
            :rtype: ProboterConfig
            """
        return await cls.filter(is_active=True).first()
