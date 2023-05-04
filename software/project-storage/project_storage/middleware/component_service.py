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

from project_storage.model import db, PcbComponent


class ComponentService:
    """
    Service that offers access to query and modify component instances
    """
    log = logging.getLogger(__name__)

    @classmethod
    def get_component_by_id(cls, component_id: int) -> PcbComponent:
        """
        Returns the pin associated with the given component_id
        """
        return PcbComponent.query.filter_by(id=component_id).one()

    @classmethod
    def create_new_component(cls, component: PcbComponent) -> PcbComponent:
        """
        Create a new component instance

        :param component: The component instance with the desired attributes
        :type component: PcbComponent
        :return: The stored PcbComponent
        :rtype: PcbComponent
        """
        cls.log.info("Creating new PcbComponent: %s", component)

        db.session.add(component)
        db.session.commit()
        return component

    @classmethod
    def update_component(cls, component: PcbComponent) -> PcbComponent:
        """
        Update an existing PcbComponent

        :param component: PcbComponent to update
        :type component: PcbComponent
        :return: The updated PcbComponent
        :rtype: PcbComponent
        """
        if component.id is None:
            msg = "PcbComponent has no ID"
            cls.log.error(msg)
            raise Exception(msg)

        cls.log.info("Updating component with ID %d: %s",
                     component.id, component)
        db.session.add(component)
        db.session.commit()

        return component

    @classmethod
    def delete_component_by_id(cls, component_id: int) -> None:
        """
        Deletes the component associated with the given pin_id

        :param component_id: Unique identifier of the PcbComponent to delete
        :type component_id: int
        """
        component = PcbComponent.query.filter_by(id=component_id).one()

        cls.log.info("Deleting PcbComponent with ID %d", component_id)
        db.session.delete(component)
        db.session.commit()
