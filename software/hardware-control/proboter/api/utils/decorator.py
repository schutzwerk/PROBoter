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

import functools

from quart import current_app

from proboter.model import ProbeType
from proboter.hardware import LightController, SignalMultiplexer, \
    UartInterfaceAdapter, TargetPowerController, Probe, StaticCamera

from .exceptions import ApiException


def inject_event_bus():
    """
    Inject the global event bus instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            event_bus = current_app.event_bus
            return await func(event_bus, *args, **kwargs)
        return wrapped
    return inner


def inject_proboter():
    """
    Inject the current PROBoter hardware instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            if current_app.proboter is None:
                raise ApiException("PROBoter not initialized")
            return await func(current_app.proboter, *args, **kwargs)
        return wrapped
    return inner


def inject_light_controller(must_be_connected: bool = True):
    """
    Inject the current light controller instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            light_controller: LightController = current_app.proboter.light_controller
            if light_controller is None:
                raise ApiException("PROBoter has no light controller")
            if must_be_connected and not light_controller.status.connected:
                raise ApiException("Light controller not connected")
            return await func(light_controller, *args, **kwargs)
        return wrapped
    return inner


def inject_power_controller(must_be_connected: bool = True):
    """
    Inject the current target power controller instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            power_controller: TargetPowerController = current_app.proboter.target_power_controller
            if power_controller is None:
                raise ApiException("PROBoter has no target power controller")
            if must_be_connected and not power_controller.status.connected:
                raise ApiException("Target power controller not connected")
            return await func(power_controller, *args, **kwargs)
        return wrapped
    return inner


def inject_signal_multiplexer(must_be_connected: bool = True):
    """
    Inject the current signal multiplexer instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            signal_multiplexer: SignalMultiplexer = current_app.proboter.signal_multiplexer
            if signal_multiplexer is None:
                raise ApiException("PROBoter has no signal multiplexer")
            if must_be_connected and not signal_multiplexer.status.connected:
                raise ApiException("Signal multiplexer not connected")
            return await func(signal_multiplexer, *args, **kwargs)
        return wrapped
    return inner


def inject_uart_interface(must_be_connected: bool = True):
    """
    Inject the current UART interface adapter instance
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            uart_interface: UartInterfaceAdapter = current_app.proboter.uart_interface_adapter
            if uart_interface is None:
                raise ApiException("PROBoter has no UART interface adapter")
            if must_be_connected and not uart_interface.status.connected:
                raise ApiException("UART interface adapter not connected")
            return await func(uart_interface, *args, **kwargs)
        return wrapped
    return inner


def inject_probe(must_be_connected: bool = True):
    """
    Inject the probe specified by its type
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(probe_type, *args, **kwargs):
            try:
                probe_type_val = ProbeType(probe_type)
            except ValueError as exc:
                raise ApiException("Invalid probe type") from exc

            probe: Probe = current_app.proboter.get_probe_by_type(
                probe_type_val)
            if probe is None:
                raise ApiException(f"PROBoter has no probe {probe_type_val}")
            if must_be_connected and not probe.status.connected:
                raise ApiException(f"Probe {probe_type_val} not connected")
            return await func(probe, *args, **kwargs)
        return wrapped
    return inner


def inject_static_camera(must_be_connected: bool = True):
    """
    Inject the static camera system specified by its index
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(camera_idx, *args, **kwargs):
            if not 0 <= camera_idx < len(current_app.proboter.static_cameras):
                raise ApiException("Invalid static camera index")

            camera: StaticCamera = current_app.proboter.static_cameras[camera_idx]
            if must_be_connected and not camera.status.connected:
                raise ApiException("Static camera not connected")
            return await func(camera, *args, **kwargs)
        return wrapped
    return inner


def inject_task_processor():
    """
    Inject the global task processor
    """
    def inner(func):
        @functools.wraps(func)
        async def wrapped(*args, **kwargs):
            return await func(current_app.task_processor, *args, **kwargs)
        return wrapped
    return inner
