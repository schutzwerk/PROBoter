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

import logging

from project_storage.model import Pin, db


class PinService:
    """
    Service that offers access to query and modify pin instances
    """
    log = logging.getLogger(__name__)

    @classmethod
    def get_pin_by_id(cls, pin_id: int) -> Pin:
        """
        Returns the pin associated with the given pin_id
        """
        return Pin.query.filter_by(id=pin_id).one()

    @classmethod
    def create_new_pin(cls, pin: Pin) -> Pin:
        """
        Create a new pin instance

        :param pin: The pin instance with the desired attributes
        :type pin: Pin
        :return: The stored Pin
        :rtype: Pin
        """
        cls.log.info("Creating new Pin: %s", pin)

        db.session.add(pin)
        db.session.commit()
        return pin

    @classmethod
    def update_pin(cls, pin: Pin) -> Pin:
        """
        Update an existing Pin

        :param pin: Pin to update
        :type pin: Pin
        :return: The updated Pin
        :rtype: Pin
        """
        if pin.id is None:
            msg = "Pin has no ID"
            cls.log.error(msg)
            raise Exception(msg)

        cls.log.info("Updating pin with ID %d: %s", pin.id, pin)
        db.session.add(pin)
        db.session.commit()

        return pin

    @classmethod
    def delete_pin_by_id(cls, pin_id: int) -> None:
        """
        Deletes the pin associated with the given pin_id

        :param pin_id: Unique identifier of the Pin to delete
        :type pin_id: int
        """
        pin = Pin.query.filter_by(id=pin_id).one()

        cls.log.info("Deleting Pin with ID %d", pin_id)
        db.session.delete(pin)
        db.session.commit()
