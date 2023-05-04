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
from typing import Callable, Iterable, Optional

import pyudev


class UsbMonitor:
    """
    USB device monitor

    This class contains several static methods to query connected
    USB devices or dynamically monitor hot-plugged devices.
    """

    logger = logging.getLogger(__module__)

    @classmethod
    def get_cameras_by_vendor(cls, vendor_id: str,
                              model_id: str) -> Iterable[str]:
        """
        Query all connected USB devices to find the device name of
        a given USB camera

        :param vendor_id: Vendor ID of the USB camera
        :type vendor_id: str
        :param model_id: Model ID of the USB camera
        :type model_id: str
        :return The USB device name / path
        :rtype: str
        """
        context = pyudev.Context()
        cls.logger.debug('Querying USB video devices')

        usb_cameras = []
        for device in context.list_devices(subsystem='video4linux'):
            dev_vendor_id = device.get('ID_VENDOR_ID')
            dev_model_id = device.get('ID_MODEL_ID')
            devname: str = device.get('DEVNAME')
            capabilities = device.get('ID_V4L_CAPABILITIES')

            if dev_vendor_id == vendor_id and dev_model_id == model_id and \
               'capture' in capabilities:
                cls.logger.info('USB camera %s:%s found at %s',
                                vendor_id, model_id, devname)
                usb_cameras.append(devname)

        return tuple(usb_cameras)

    @classmethod
    def get_serials_by_vendor(cls, vendor_id: str,
                              model_id: str) -> Iterable[str]:
        """
        Query all connected USB devices to find the device name of
        a given USB serial device

        :param vendor_id: Vendor ID of the USB serial device
        :type vendor_id: str
        :param model_id: Model ID of the USB serial device
        :type model_id: str
        :return: The device name / path. If no USB device matching the vendor
                 and model ID was found, None is returned.
        :rtype: str
        """
        context = pyudev.Context()
        cls.logger.debug(
            'Querying USB serial devices for %s:%s', vendor_id, model_id)

        usb_serials = []
        for subsystem in ('usb-serial', 'tty'):
            for device in context.list_devices(subsystem=subsystem):
                dev_vendor_id = device.get('ID_VENDOR_ID')
                dev_model_id = device.get('ID_MODEL_ID')
                devname = device.get('DEVNAME')

                if dev_vendor_id == vendor_id and dev_model_id == model_id:
                    cls.logger.info('USB serial %s:%s found at %s',
                                    vendor_id, model_id, devname)
                    usb_serials.append(devname)

        return tuple(usb_serials)

    @classmethod
    def create_camera_monitor(cls, vendor_id: str, model_id: str,
                              callback: Callable[[str, str], None]) -> pyudev.MonitorObserver:
        """
        Create a monitor object that executes a given callback function every
        time the specified USB camera is (dis-)connected to the host

        :param vendor_id: Vendor ID of the USB camera
        :type vendor_id: str
        :param model_id: Model ID of the USB camera
        :type model_id: str
        :param callback: The callback that is executed when an USB camera
                         with the given vendor / model ID is (dis-) connected.
                         The first argument to the callback is an action string
                         (e.g. 'add' if a new USB device has been connected). As
                         second argument the device name / path is passed to the
                         callback.
        :type callback: [Callable[(str, str),...]]
        :return: The created monitor object
        :rtype: pyudev.MonitorObserver
        """
        # Create an USB monitor
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('video4linux')

        # Set up a filtered callback
        def on_event(action, device):
            dev_vendor_id = device.get('ID_VENDOR_ID')
            dev_model_id = device.get('ID_MODEL_ID')
            devname = device.get('DEVNAME')
            capabilities = device.get('ID_V4L_CAPABILITIES')

            if dev_vendor_id == vendor_id and dev_model_id == model_id \
               and 'capture' in capabilities:
                cls.logger.info('USB camera %s at %s',
                                'added' if action == 'add' else 'removed', devname)
                # Execute the given callback
                callback(action, devname)

        return pyudev.MonitorObserver(monitor, on_event)

    @classmethod
    def create_serial_monitor(cls, callback: Callable[[str, str], None],
                              vendor_id: Optional[str] = None,
                              model_id: Optional[str] = None,
                              device_name: Optional[str] = None) -> pyudev.MonitorObserver:
        """
        Create a monitor object that executes a given callback function every
        time the specified USB serial device is (dis-)connected to the host

        :param vendor_id: Vendor ID of the USB serial device, defaults to None
        :type vendor_id: Optional[str]
        :param model_id: Model ID of the USB serial device, defaults to None
        :type model_id: Optional[str]
        :param device_name: USB serial device name, defaults to None
        :type device_name: Optional[str]
        :param callback: The callback that is executed when an USB serial
                         with the given vendor / model ID is (dis-) connected.
                         The first argument to the callback is an action string
                         (e.g. 'add' if a new USB device has been connected). As
                         second argument the device name / path is passed to the
                         callback.
        :type callback: [Callable[(str, str),...]]
        :return: The created monitor object
        :rtype: pyudev.MonitorObserver
        """
        # Create an USB monitor
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by('tty')

        # Set up a filtered callback
        def on_event(action, device):
            dev_vendor_id = device.get('ID_VENDOR_ID').lower()
            dev_model_id = device.get('ID_MODEL_ID').lower()
            dev_name = device.get('DEVNAME').lower()

            is_match = True
            if vendor_id is not None and dev_vendor_id != vendor_id.lower():
                is_match = False
            if model_id is not None and dev_model_id != model_id.lower():
                is_match = False
            if device_name is not None and dev_name != device_name.lower():
                is_match = False

            if is_match:
                callback(action, dev_name)

        return pyudev.MonitorObserver(monitor, on_event)
