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

class ProboterException(Exception):
    """
    Base class for all Proboter hardware related exceptions
    """


class AxesControllerException(ProboterException):
    """
    Base class for all axes unit related exceptions
    """


class AxesControllerConnectionException(AxesControllerException):
    """
    Exception that indicates an error in the serial connection
    to the controller board
    """


class UartInterfaceAdapterConnectionException(ProboterException):
    """
    Exception that indicates an error in the serial connection
    to the UART interface adapter
    """


class CameraException(ProboterException):
    """
    Base class for all camera related exceptions
    """


class CameraNotConnectedException(CameraException):
    """
    Exception that is raised if the camera is accessed while the physical
    device is not connected
    """


class ProbeException(ProboterException):
    """
    Base class for all probe related exceptions
    """


class SignalMultiplexerException(ProboterException):
    """
    Base class for all exceptions related to the signal multiplexer board
    """


class TargetPowerControllerException(ProbeException):
    """
    Base class for all target power controller related exceptions
    """


class TargetPowerControllerNotConnectedException(
        TargetPowerControllerException):
    """
    Exception that is raised if the target power controller is accessed
    while the physical is not connected
    """
