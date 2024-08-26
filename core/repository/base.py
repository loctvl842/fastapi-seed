from functools import reduce
from typing import Any, Dict, Generic, Optional, Sequence, Type, TypeVar

from sqlalchemy import Select, delete, func, inspect, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.db import Base
from core.exceptions import SystemException

from .enum import SynchronizeSessionEnum

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.session = db_session
        self.model_class = model

    def _query(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
        join_: set[str] | None = None,
        order_: dict | None = None,
        where_: Optional[list] = None,
    ) -> Select:
        """
        Returns a callable that can be used to query the model.

        :param join_: The joins to make.
        :param order_: The order of the results. (e.g desc, asc)
        :return: A callable that can be used to query the model.
        """
        if fields:
            query = select(*fields)
        else:
            query = select(self.model_class)
        if where_:
            for condition in where_:
                query = query.where(condition)
        if distinct_:
            query = query.distinct(*distinct_)

        if skip is not None:
            query = query.offset(skip)
        if limit is not None:
            query = query.limit(limit)
        query = self._maybe_join(query, join_)
        query = self._maybe_ordered(query, order_)

        return query

    def _maybe_join(self, query: Select, join_: Optional[set[str]] = None) -> Select:
        """
        Returns the query with the given joins.

        :param query: The query to join.
        :param join_: The joins to make.
        :return: The query with the given joins.
        """
        if not join_:
            return query

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
                    if isinstance(order, str):
                        query = query.order_by(getattr(self.model_class, order).asc())
                    elif isinstance(order, dict):
                        model_class = order.get("model_class", self.model_class)
                        field = order.get("field", None)
                        if field is None:
                            raise SystemException("Missing field in order")
                        query = query.order_by(getattr(model_class, field).asc())
                    else:
                        raise SystemException("Order params must be string or dict")
            else:
                for order in order_["desc"]:
                    if isinstance(order, str):
                        query = query.order_by(getattr(self.model_class, order).desc())
                    elif isinstance(order, dict):
                        model_class = order.get("model_class", self.model_class)
                        field = order.get("field", None)
                        if field is None:
                            raise SystemException("Missing field in order")
                        query = query.order_by(getattr(model_class, field).desc())
                    else:
                        raise SystemException("Order params must be string or dict")

        return query

    async def _count(self, query: Select) -> int:
        """
        Returns the count of the records.

        :param query: The query to execute.
        """
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()

    async def _all(self, query: Select) -> list[ModelType]:
        """
        Returns all results from the query.

        :param query: The query to execute.
        :return: A list of model instances.
        """
        response = await self.session.scalars(query)
        return list(response.all())

    async def _all_unique(self, query: Select) -> Sequence[ModelType]:
        result = await self.session.execute(query)
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

    async def create(self, attributes: Optional[dict[str, Any]] = None, commit=False) -> ModelType:
        """
        Creates the model instance.

        :param attributes: The attributes to create the model with.
        :return: The created model instance.
        """
        if attributes is None:
            attributes = {}
        model = self.model_class(**attributes)
        self.session.add(model)
        if commit:
            await self.session.commit()
        return model

    async def create_many(self, attributes_list: list[dict[str, Any]], commit=False) -> Sequence[ModelType]:
        """
        Creates multiple model instances.

        :param entities: The list of attributes for the model instances to create.
        :param commit: Whether to commit the transaction after creation.
        :return: The list of created model instances.
        """
        stmt = insert(self.model_class).values(attributes_list).returning(self.model_class)
        result = await self.session.execute(stmt)
        created_instances = result.scalars().all()
        if commit:
            await self.session.commit()
        return created_instances

    async def update(self, where_: list[Any], attributes: Dict[str, Any], commit=False) -> ModelType:
        """
        Updates the model instance.

        :param attributes: The attributes to update the model with.
        :param commit: Whether to commit the changes to the database.
        :return: The updated model instance.
        """
        query = update(self.model_class)
        for condition in where_:
            query = query.where(condition)
        query = query.values(**attributes).returning(self.model_class)

        result = await self.session.execute(query)
        if commit:
            await self.session.commit()

        return result.scalars().first()


    async def upsert(self, index_elements: list[str], attributes: Dict[str, Any], commit=False) -> Optional[ModelType]:
        """
        Creates or updates the model instance. Using on_conflict_do_update

        :param model_id: The ID of the model instance to update.
        :param attributes: The attributes to update the model with.
        :param commit: Whether to commit the changes to the database.
        :return: The updated model instance.
        """
        mapper = inspect(self.model_class)
        columns = mapper.columns.keys()
        if "updated_at" in columns:
            attributes["updated_at"] = func.now()

        stmt = (
            insert(self.model_class)
            .values(**attributes)
            .on_conflict_do_update(index_elements=index_elements, set_={k: attributes[k] for k in attributes})
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)

        if commit:
            await self.session.commit()
        return result.scalars().first()

    async def upsert_many(
        self, index_elements: list[str], attributes_list: list[dict[str, Any]], commit=False
    ) -> Sequence[ModelType]:
        """
        Upserts multiple model instances.

        :param index_elements: The list of index elements to upsert.
        :param attributes_list: The list of attributes for the model instances to upsert.
        :param commit: Whether to commit the changes to the database.
        :return: The list of upserted model instances.
        """
        mapper = inspect(self.model_class)
        columns = mapper.columns.keys()
        if "updated_at" in columns:
            attributes_list = [{**attributes, "updated_at": func.now()} for attributes in attributes_list]

        stmt = (
            insert(self.model_class)
            .values(attributes_list)
            .on_conflict_do_update(
                index_elements=index_elements,
                set_={col: getattr(insert(self.model_class).excluded, col) for col in attributes_list[0]},
            )
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)

        if commit:
            await self.session.commit()
        return result.scalars().all()

    async def count(self, where_: Optional[list] = None) -> int:
        """
        Returns the number of records in the DB.
        :return: The number of records.
        """
        query = self._query(where_=where_)
        return await self._count(query)

    async def get_all(
        self,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
        where_: Optional[list] = None,
    ) -> list[ModelType]:
        query = self._query(join_=join_, order_=order_, where_=where_)
        return await self._all(query)

    async def get_many(
        self,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
        where_: Optional[list] = None,
    ) -> Sequence[ModelType]:
        """
        Returns a list of records based on pagination params.

        :param skip: The number of records to skip.
        :param limit: The number of records to return.
        :param join_: The joins to make.
        :return: A list of records.
        """

        query = self._query(skip=skip, limit=limit, fields=fields, distinct_=distinct_, join_=join_, order_=order_, where_=where_)
        result = await self.session.scalars(query)
        return result.all()

    async def get_by(
        self,
        field: str,
        value: str,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        join_: Optional[set[str]] = None,
    ) -> Sequence[ModelType]:
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
        field: Optional[str] = None,
        value: str | None = None,
        where_: Optional[list] = None,
        skip: Optional[int] = None,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
    ) -> ModelType | None:
        """
        Returns the first model instance matching the field.
        :param field: The field to match.
        :param value: The value to match.
        :param join_: The joins to make.
        :return: The first model instance matching the field.
        """
        query = self._query(skip=skip, join_=join_, order_=order_, where_=where_)
        if field and value:
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
        result = await self.session.scalars(query)
        return bool(result.first())

    async def delete(self, model: ModelType) -> None:
        return await self.session.delete(model)

    async def delete_many(
        self,
        where_: Optional[list] = None,
        synchronize_session: SynchronizeSessionEnum = SynchronizeSessionEnum.FALSE,
    ):
        query = delete(self.model_class)
        if where_ is not None:
            for condition in where_:
                query = query.where(condition)
        query = query.execution_options(synchronize_session=synchronize_session.value)
        return await self.session.execute(query)
