from functools import reduce
from typing import Any, Generic, Sequence, Type, TypeVar

from sqlalchemy import Select, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base

from .enum import SynchronizeSessionEnum

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.session = db_session
        self.model_class = model

    def _query(
        self,
        skip: int = None,
        limit: int = None,
        join_: set[str] | None = None,
        order_: dict | None = None,
        where_: list = None,
    ) -> Select:
        """
        Returns a callable that can be used to query the model.

        :param join_: The joins to make.
        :param order_: The order of the results. (e.g desc, asc)
        :return: A callable that can be used to query the model.
        """
        query = select(self.model_class)
        if where_:
            for condition in where_:
                query = query.where(condition)

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        query = self._maybe_join(query, join_)
        query = self._maybe_ordered(query, order_)

        return query

    def _maybe_join(self, query: Select, join_: set[str] | None = None) -> Select:
        """
        Returns the query with the given joins.

        :param query: The query to join.
        :param join_: The joins to make.
        :return: The query with the given joins.
        """
        if not join_:
            return query

        if not isinstance(join_, set):
            raise TypeError("join_ must be a set")

        return reduce(self._add_join_to_query, join_, query)

    def _add_join_to_query(self, query: Select, join_: str) -> Select:
        """
        Returns the query with the given join.

        :param query: The query to join.
        :param join_: The join to make.
        :return: The query with the given join.
        """
        return getattr(self, "_join_" + join_)(query)

    def _maybe_ordered(self, query: Select, order_: dict | None = None) -> Select:
        """
        Returns the query ordered by the given column.

        :param query: The query to order.
        :param order_: The order to make.
        :return: The query ordered by the given column.
        """
        if order_:
            if order_.get("asc", None) is not None:
                for order in order_["asc"]:
                    query = query.order_by(getattr(self.model_class, order).asc())
            else:
                for order in order_["desc"]:
                    query = query.order_by(getattr(self.model_class, order).desc())

        return query

    async def _count(self, query: Select) -> int:
        """
        Returns the count of the records.

        :param query: The query to execute.
        """
        query = await self.session.scalars(select(func.count()).select_from(query))
        return query.one()

    async def _all(self, query: Select) -> list[ModelType]:
        """
        Returns all results from the query.

        :param query: The query to execute.
        :return: A list of model instances.
        """
        response = await self.session.scalars(query)
        return list(response.all())

    async def _all_unique(self, query: Select) -> list[ModelType]:
        result = self.session.execute(query)
        return result.unique().scalars().all()

    async def _get_by(self, query: Select, field: str, value: str) -> Select:
        """
        Returns the query filtered by the given column.

        :param query: The query to filter.
        :param field: The column to filter by.
        :param value: The value to filter by.
        :return: The filtered query.
        """
        return query.where(getattr(self.model_class, field) == value)

    async def create(self, attributes: dict[str, Any] = None) -> ModelType:
        """
        Creates the model instance.

        :param attributes: The attributes to create the model with.
        :return: The created model instance.
        """
        if attributes is None:
            attributes = {}
        model = self.model_class(**attributes)
        self.session.add(model)
        return model

    async def count(self, where_: list = None) -> int:
        """
        Returns the number of records in the DB.
        :return: The number of records.
        """
        query = self._query(where_=where_)
        return await self._count(query)

    async def get_all(self, join_: set[str] | None = None) -> list[ModelType]:
        query = self._query(join_=join_)
        return await self._all(query)

    async def get_many(
        self,
        skip: int = None,
        limit: int = None,
        join_: set[str] | None = None,
        order_: dict | None = None,
        where_: list = None,
    ) -> Sequence[ModelType]:
        """
        Returns a list of records based on pagination params.

        :param skip: The number of records to skip.
        :param limit: The number of records to return.
        :param join_: The joins to make.
        :return: A list of records.
        """

        query = self._query(skip=skip, limit=limit, join_=join_, order_=order_, where_=where_)
        result = await self.session.scalars(query)
        return result.all()

    async def get_by(
        self,
        field: str,
        value: str,
        skip: int = None,
        limit: int = None,
        join_: set[str] | None = None,
    ) -> list[ModelType]:
        """
        Returns the model instance matching the field.
        :param field: The field to match.
        :param value: The value to match.
        :param join_: The joins to make.
        :return: list of model instances matching the field.
        """
        query = self._query(skip=skip, limit=limit, join_=join_)
        query = await self._get_by(query, field, value)
        if join_ is not None:
            return await self._all_unique(query)
        return await self._all(query)

    async def first(self, join_: set[str] | None = None) -> ModelType | None:
        """
        Returns the first model instance.
        :param join_: The joins to make.
        :return: The first model instance.
        """
        query = self._query(join_=join_)
        query = query.limit(1)
        query = await self.session.scalars(query)
        return query.first()

    async def first_by(
        self,
        field: str,
        value: str,
        skip: int = None,
        join_: set[str] | None = None,
        order_: dict | None = None,
    ) -> ModelType | None:
        """
        Returns the first model instance matching the field.
        :param field: The field to match.
        :param value: The value to match.
        :param join_: The joins to make.
        :return: The first model instance matching the field.
        """
        query = self._query(skip=skip, join_=join_, order_=order_)
        query = await self._get_by(query, field, value)
        query = await self.session.scalars(query)
        return query.first()

    async def exists(self, field: str, value: str) -> bool:
        """
        Returns whether the model instance exists.
        :param field: The field to match.
        :param value: The value to match.
        :return: Whether the model instance exists.
        """
        query = select(self.model_class).where(getattr(self.model_class, field) == value)
        return bool(await self.session.scalars(query).first())

    async def delete(self, model: ModelType) -> None:
        return await self.session.delete(model)

    async def delete_many(
        self,
        where_: list = None,
        synchronize_session: SynchronizeSessionEnum = False,
    ):
        query = delete(self.model_class)
        if where_ is not None:
            for condition in where_:
                query = query.where(condition)
        query = query.execution_options(synchronize_session=synchronize_session)
        return await self.session.execute(query)
