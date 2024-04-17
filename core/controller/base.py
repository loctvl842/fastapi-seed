from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from core.db import Base, Transactional
from core.exceptions import NotFoundException
from core.repository import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseController(Generic[ModelType]):
    """Data class for base controller."""

    def __init__(self, model_class: Type[ModelType], repository: BaseRepository) -> None:
        self.model_class = model_class
        self.repository = repository

    async def count(self, where_: list = None) -> int:
        """
        Returns the number of records in the DB.
        :return: The number of records.
        """
        return await self.repository.count(where_)

    async def get_by_id(self, id_: int | UUID, join_: set[str] | None = None) -> ModelType:
        """
        Returns the model instance matching the id.

        :param id_: The id to match.
        :param join_: The joins to make.
        :return: The model instance.
        """

        db_obj = await self.repository.first_by(field="id", value=id_, join_=join_, unique=True)
        if not db_obj:
            raise NotFoundException(f"{self.model_class.__tablename__.title()} with id: {id} does not exist")

        return db_obj

    async def get_many(
        self,
        skip: int = None,
        limit: int = None,
        join_: set[str] | None = None,
        order_: dict | None = None,
        where_: list = None,
    ):
        """
        Returns a list of records based on pagination params.

        :param skip: The number of records to skip.
        :param limit: The number of records to return.
        :param join_: The joins to make.
        :return: A list of records.
        """
        response = await self.repository.get_many(skip, limit, join_, order_, where_)
        return response

    async def get_all(self, join_: set[str] | None = None) -> list[ModelType]:
        response = await self.repository.get_all(join_)
        return response

    @Transactional()
    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """
        Creates a new Object in the DB.

        :param attributes: The attributes to create the object with.
        :return: The created object.
        """
        create = await self.repository.create(attributes)
        return create

    @Transactional()
    async def delete(self, model: ModelType) -> None:
        """
        Deletes the Object from the DB.

        :param model: The model to delete.
        :return: True if the object was deleted, False otherwise.
        """
        delete = await self.repository.delete(model)
        return delete

    @Transactional()
    async def delete_many(
        self,
        where_: list = None,
    ):
        """
        Deletes multiple objects from the DB.
        :param where_: The conditions to match.
        :return: True if the objects were deleted, False otherwise.
        """
        await self.repository.delete_many(where_)
        delete = await self.repository.get_many(where_=where_)
        return delete

    @Transactional()
    async def delete_by_id(self, id_: int | UUID) -> None:
        """
        Deletes the Object from the DB.
        :param id_: The id to delete.
        :return: True if the object was deleted, False otherwise.
        """
        await self.repository.delete_many(where_=[self.model_class.id == id_])
        delete = await self.repository.first_by(field="id", value=id_)
        return delete
