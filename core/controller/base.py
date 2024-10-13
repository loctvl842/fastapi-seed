from typing import Any, Generic, Optional, Sequence, Type, TypeVar

from core.db import Base, Transactional
from core.exceptions import NotFoundException
from core.repository import BaseRepository
from core.repository.enum import SynchronizeSessionEnum

ModelType = TypeVar("ModelType", bound=Base)


class BaseController(Generic[ModelType]):
    """Data class for base controller."""

    def __init__(self, model_class: Type[ModelType], repository: BaseRepository) -> None:
        self.model_class = model_class
        self.repository = repository

    async def count(
        self,
        *,
        where_: Optional[list] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
    ) -> int:
        """
        Returns the number of records in the DB.
        """
        return await self.repository.count(where_=where_, fields=fields, distinct_=distinct_)

    async def get_many(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
        where_: Optional[list] = None,
        group_by_: Optional[list] = None,
    ):
        """
        Returns a list of records based on pagination params.
        """
        response = await self.repository.get_many(
            skip=skip,
            limit=limit,
            fields=fields,
            distinct_=distinct_,
            join_=join_,
            order_=order_,
            where_=where_,
            group_by_=group_by_,
        )
        return response

    @Transactional()
    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """
        Creates a new Object in the DB.
        """
        create = await self.repository.create(attributes=attributes)
        return create

    @Transactional()
    async def create_many(self, attributes_list: list[dict[str, Any]]) -> Sequence[ModelType]:
        """
        Create multiple objects in the DB.
        """
        creates = await self.repository.create_many(attributes_list)
        return creates

    @Transactional()
    async def upsert(self, index_elements: list[str], attributes: dict[str, Any]) -> Optional[ModelType]:
        return await self.repository.upsert(index_elements, attributes)

    @Transactional()
    async def upsert_many(self, index_elements: list[str], attributes_list: list[dict[str, Any]]):
        return await self.repository.upsert_many(index_elements, attributes_list)

    @Transactional()
    async def delete(
        self,
        where_: Optional[list] = None,
        *,
        synchronize_session: SynchronizeSessionEnum = SynchronizeSessionEnum.FALSE,
    ) -> None:
        """
        Deletes the Object from the DB.
        """
        delete = await self.repository.delete(where_=where_, synchronize_session=synchronize_session)
        return delete
