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

from typing import Iterable, TypeVar, Type

from tortoise import fields
from tortoise.models import Model

T = TypeVar('T')


class EntityNotFoundException(Exception):
    """
    Exception that is raised if a requested entity could not be found
    """


class Entity(Model):
    """
    Base class for all data model / entity classes

    The class provides common methods for entity handling
    """
    # Unique ID of the entity
    id: int = fields.IntField(pk=True)
    # Entity creation timestamp
    time_created = fields.DatetimeField(auto_now_add=True)
    # Entity last modification timestamp
    time_updated = fields.DatetimeField(auto_now=True)

    @classmethod
    async def get_by_id(cls: Type[T], entity_id: int) -> T:
        """
        Return an entity with a given ID
        """
        entitiy = await cls.filter(id=entity_id).get_or_none()
        if entitiy is None:
            raise EntityNotFoundException()
        return entitiy

    @classmethod
    async def delete_by_id(cls, entity_id: int) -> None:
        """
        Delete an entity with a specific ID
        """
        entity = await cls.get_by_id(entity_id)
        if entity is not None:
            await entity.delete()

    @classmethod
    async def get_all(cls: Type[T]) -> Iterable[T]:
        """
        Return all entities of the current class / type
        """
        return await cls.all()
