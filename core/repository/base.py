import traceback
from functools import reduce, wraps
from typing import Any, Awaitable, Callable, Dict, Generic, Optional, ParamSpec, Sequence, Type, TypeVar

from sqlalchemy import Select, delete, func, inspect, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.db import Base
from core.exceptions import SystemException
from core.logger import syslog

from .enum import SynchronizeSessionEnum

ModelType = TypeVar("ModelType", bound=Base)

P = ParamSpec("P")
R = TypeVar("R")


def safeguard_db_ops():
    """A decorator to safeguard database operations and handle exceptions."""

    def decorator(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            try:
                return await fn(*args, **kwargs)
            except SQLAlchemyError as e:
                msg = f"An error occurred while executing the database operation: {e}"
                syslog.error(msg)
                traceback.print_exc()
                raise SystemException(msg)

        return wrapper

    return decorator


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.session = db_session
        self.model_class = model

    @safeguard_db_ops()
    async def _query(
        self,
        *,
        skip: Optional[int] = None,
        limit: Optional[int] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
        where_: Optional[list] = None,
        group_by_: Optional[list] = None,
    ) -> Select:
        """
        Constructs and returns a SQL query based on the provided parameters.

        This method builds a SQLAlchemy `Select` object by applying various clauses such as
        `WHERE`, `DISTINCT`, `OFFSET`, `LIMIT`, `JOIN`, `ORDER BY`, and `GROUP BY` based
        on the input arguments. It allows for flexible querying of the associated model.

        Args:
            skip (Optional[int], optional):
                The number of records to skip in the result set. Defaults to `None`.
            limit (Optional[int], optional):
                The maximum number of records to return. Defaults to `None`.
            fields (Optional[List[str]], optional):
                A list of fields/columns to include in the `SELECT` statement.
                If not provided, all fields of the model are selected. Defaults to `None`.
            distinct_ (Optional[List[str]], optional):
                A list of fields to apply the `DISTINCT` clause on, ensuring unique results
                based on these fields. Defaults to `None`.
            join_ (Optional[Dict[str, Any]], optional):
                A dictionary specifying the joins to make. Each key should correspond to a valid
                relationship defined in the model, and the value can provide additional
                parameters for the join operation. Defaults to `None`.
            order_ (Optional[Dict[str, Any]], optional):
                A dictionary specifying the order of the results. It should contain either
                an `'asc'` key with a list of fields to sort in ascending order or a `'desc'`
                key with a list of fields to sort in descending order. Each field can be a
                string representing the field name or a dictionary with additional parameters,
                such as specifying a different model class. Defaults to `None`.
            where_ (Optional[List[Any]], optional):
                A list of conditions to apply in the `WHERE` clause of the query. Each condition
                should be a valid SQLAlchemy filter expression. Defaults to `None`.
            group_by_ (Optional[List[str]], optional):
                A list of fields to group the results by, applying the `GROUP BY` clause.
                Defaults to `None`.

        Returns:
            Select:
                A SQLAlchemy `Select` object representing the constructed query, which can be
                executed to retrieve the desired records from the database.

        Raises:
            SystemException:
                If there are issues with constructing the query, such as missing fields in
                ordering parameters.

        Example:
            ```python
            query = await self._query(
                skip=10,
                limit=5,
                fields=['id', 'name'],
                distinct_=['email'],
                join_={'orders': {'type': 'left'}},
                order_={'asc': ['name'], 'desc': ['created_at']},
                where_=[User.active == True],
                group_by_=['id']
            )
            results = await session.execute(query)
            users = results.scalars().all()
            ```
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
        if group_by_:
            query = query.group_by(*group_by_)

        return query

    def _maybe_join(self, query: Select, join_: Optional[dict] = None) -> Select:
        """
        Applies the specified joins to the given SQL query.

        This method iterates over the provided `join_` dictionary and applies each join
        to the SQLAlchemy `Select` query object using the `_add_join_to_query` helper method.
        """
        if not join_:
            return query

        return reduce(self._add_join_to_query, join_.items(), query)

    def _add_join_to_query(self, query: Select, join_: tuple) -> Select:
        """
        Applies a single join to the SQL query based on the provided join item.

        This helper method takes a tuple containing the join key and its associated parameters,
        constructs the appropriate join method name, and applies the join to the query.
        """
        key, value = join_
        return getattr(self, "_join_" + key)(query, value)

    def _maybe_ordered(self, query: Select, order_: dict | None = None) -> Select:
        """
        Applies ordering to the SQL query based on the provided order parameters.

        This method modifies the SQLAlchemy `Select` query object by adding `ORDER BY` clauses
        based on the specifications in the `order_` dictionary. It supports both ascending
        and descending orderings and handles complex ordering scenarios with additional parameters.

        Args:
            query (Select):
                The SQLAlchemy `Select` object to which the ordering will be applied.
            order_ (Optional[Dict[str, Any]], optional):
                A dictionary specifying the order of the results. It should contain either
                an `'asc'` key with a list of fields to sort in ascending order or a `'desc'`
                key with a list of fields to sort in descending order. Each field can be a
                string representing the field name or a dictionary with additional parameters,
                such as specifying a different model class. Defaults to `None`.

        Returns:
            Select:
                The modified SQLAlchemy `Select` object with the specified ordering applied.

        Example:
            ```python
            order_parameters = {
                'asc': ['name', {'field': 'created_at', 'model_class': CustomModel}]
            }
            ordered_query = self._maybe_ordered(query, order_parameters)
            ```
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

    @safeguard_db_ops()
    async def count(
        self,
        *,
        where_: Optional[list] = None,
        fields: Optional[list] = None,
        distinct_: Optional[list] = None,
    ) -> int:
        """
        Retrieves the number of records in the database that match the specified criteria.

        This method constructs a query using the provided `where_`, `fields`, and `distinct_` parameters
        by invoking the `_query` helper method. It then executes a count operation on the constructed query
        to determine the total number of matching records.

        Args:
            where_ (Optional[List[Any]], optional):
                A list of conditions to apply in the `WHERE` clause of the query.
                Each condition should be a valid SQLAlchemy filter expression.
                Defaults to `None`.
            fields (Optional[List[str]], optional):
                A list of field names to include in the `SELECT` statement.
                If not provided, all fields of the model are selected.
                Defaults to `None`.
            distinct_ (Optional[List[str]], optional):
                A list of field names to apply the `DISTINCT` clause on, ensuring unique results
                based on these fields. Defaults to `None`.

        Returns:
            int:
                The total number of records that match the query criteria.

        Raises:
            SystemException:
                If there are issues with constructing or executing the query, such as invalid fields
                or conditions.

        Example:
            ```python
            count = await self.count(
                where_=[User.active == True],
                fields=['id', 'name'],
                distinct_=['email']
            )
            print(f"Active users count: {count}")
            ```
        """
        query = await self._query(where_=where_, fields=fields, distinct_=distinct_)
        return await self._count(query)

    @safeguard_db_ops()
    async def _count(self, query: Select) -> int:
        """
        Executes a count query to determine the number of records matching the provided query.

        This method constructs a count query by wrapping the provided `Select` object as a subquery
        and applying the SQL `COUNT` function. It then executes the count query to retrieve the
        total number of matching records.
        """
        count_query = select(func.count()).select_from(query.subquery())
        result = await self.session.execute(count_query)
        return result.scalar_one()

    @safeguard_db_ops()
    async def create(self, attributes: Optional[dict[str, Any]] = None, *, commit=False) -> ModelType:
        """
        Creates and adds a new model instance to the database.

        Args:
            attributes (Optional[dict[str, Any]]): The attributes to initialize the model with.
                Defaults to an empty dictionary if not provided.
            commit (bool): Whether to commit the changes to the database immediately.
                Defaults to False.

        Returns:
            ModelType: The created model instance.
        """
        if attributes is None:
            attributes = {}
        model = self.model_class(**attributes)
        self.session.add(model)
        if commit:
            await self.session.commit()
        return model

    @safeguard_db_ops()
    async def create_many(self, attributes_list: list[dict[str, Any]], commit=False) -> Sequence[ModelType]:
        """Creates multiple model instances and adds them to the database.

        Args:
            attributes_list (list[dict[str, Any]]): A list of dictionaries, where each dictionary
                contains the attributes for one model instance.
            commit (bool): Whether to commit the transaction after creation. Defaults to False.

        Returns:
            Sequence[ModelType]: A list of the created model instances.
        """
        stmt = insert(self.model_class).values(attributes_list).returning(self.model_class)
        result = await self.session.execute(stmt)
        created_instances = result.scalars().all()

        for isntance in created_instances:
            self.session.add(isntance)

        if commit:
            await self.session.commit()
        return created_instances

    @safeguard_db_ops()
    async def update(self, where_: list[Any], attributes: Dict[str, Any], commit=False) -> ModelType:
        """Partially updates an existing model instance in the database.

        Args:
            where_ (list[Any]): A list of conditions used to identify the model instance(s) to update.
            attributes (Dict[str, Any]): A dictionary of attribute key-value pairs to update the model with.
            commit (bool): Whether to commit the changes to the database. Defaults to False.

        Returns:
            ModelType: The updated model instance.
        """
        query = update(self.model_class)
        for condition in where_:
            query = query.where(condition)
        query = query.values(**attributes).returning(self.model_class)

        result = await self.session.execute(query)
        if commit:
            await self.session.commit()

        return result.scalars().first()

    @safeguard_db_ops()
    async def upsert(
        self,
        index_elements: list[Any],
        attributes: Dict[str, Any],
        *,
        commit=False,
        eager_relations: Optional[list[str]] = None,
    ) -> Optional[ModelType]:
        """Creates or updates a model instance using `on_conflict_do_update`.

        If the model instance does not exist, it will be created. If it exists, the specified
        attributes will be updated.

        Args:
            index_elements (list[Any]): The list of index elements (columns) used to identify the
                conflict for upsert operations.
            attributes (Dict[str, Any]): A dictionary of attribute key-value pairs to create or update
                the model instance with.
            commit (bool): Whether to commit the changes to the database. Defaults to False.
            eager_relations (Optional[list[str]]): List of relations to eagerly load after upsert, if any.

        Returns:
            Optional[ModelType]: The created or updated model instance, or None if no instance is found.
        """
        mapper = inspect(self.model_class)
        columns = mapper.columns.keys()
        valid_attributes = {key: value for key, value in attributes.items() if key in columns}
        if "updated_at" in columns:
            valid_attributes["updated_at"] = func.now()

        query = (
            insert(self.model_class)
            .values(**valid_attributes)
            .on_conflict_do_update(index_elements=index_elements, set_={k: v for k, v in valid_attributes.items()})
            .returning(self.model_class)
        )
        result = await self.session.execute(query)

        if commit:
            await self.session.commit()

        instance = result.scalars().first()

        if instance and eager_relations:
            instance = await self.session.get(
                self.model_class, instance.id, options=[selectinload(relation) for relation in eager_relations]
            )
        return instance

    @safeguard_db_ops()
    async def upsert_many(
        self, index_elements: list[Any], attributes_list: list[dict[str, Any]], commit=False
    ) -> Sequence[ModelType]:
        """Upserts multiple model instances in the database.

        For each entry in the `attributes_list`, the function will either insert a new record or update
        an existing record based on conflicts with the `index_elements`.

        Args:
            index_elements (list[Any]): A list of index elements (columns) used to identify conflicts for
                upsert operations.
            attributes_list (list[dict[str, Any]]): A list of dictionaries, where each dictionary contains
                the attributes for a model instance to be upserted.
            commit (bool): Whether to commit the changes to the database. Defaults to False.

        Returns:
            Sequence[ModelType]: A list of upserted model instances.
        """
        mapper = inspect(self.model_class)
        columns = mapper.columns.keys()
        valid_attributes_list = [
            {key: value for key, value in attributes.items() if key in columns} for attributes in attributes_list
        ]

        if "updated_at" in columns:
            valid_attributes_list = [{**attributes, "updated_at": func.now()} for attributes in valid_attributes_list]

        stmt = (
            insert(self.model_class)
            .values(valid_attributes_list)
            .on_conflict_do_update(
                index_elements=index_elements,
                set_={col: getattr(insert(self.model_class).excluded, col) for col in valid_attributes_list[0]},
            )
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)

        if commit:
            await self.session.commit()
        return result.scalars().all()

    @safeguard_db_ops()
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
    ) -> Sequence[ModelType]:
        """Retrieves a list of records based on various query parameters.

        Supports pagination, filtering, ordering, joining, and grouping of records.

        Args:
            skip (Optional[int]): The number of records to skip. Used for pagination.
            limit (Optional[int]): The maximum number of records to return. Used for pagination.
            fields (Optional[list]): A list of specific fields to retrieve from the records.
            distinct_ (Optional[list]): A list of fields to apply distinct filtering on.
            join_ (Optional[set[str]]): A set of related tables to join with the query.
            order_ (Optional[dict]): A dictionary specifying the fields and their order (ASC/DESC).
            where_ (Optional[list]): A list of conditions to filter the records.
            group_by_ (Optional[list]): A list of fields to group the results by.

        Returns:
            Sequence[ModelType]: A list of model instances that match the query parameters.
        """

        query = await self._query(
            skip=skip,
            limit=limit,
            fields=fields,
            distinct_=distinct_,
            join_=join_,
            order_=order_,
            where_=where_,
            group_by_=group_by_,
        )
        result = await self.session.scalars(query)
        return result.all()

    @safeguard_db_ops()
    async def first(
        self,
        fields: Optional[list] = None,
        where_: Optional[list] = None,
        skip: Optional[int] = None,
        join_: Optional[set[str]] = None,
        order_: Optional[dict] = None,
        relations: Optional[list[str]] = None,
    ) -> ModelType | None:
        """Retrieves the first model instance that matches the specified query parameters.

        Args:
            fields (Optional[list]): A list of specific fields to retrieve from the model.
            where_ (Optional[list]): A list of conditions to filter the records.
            skip (Optional[int]): The number of records to skip, useful for pagination.
            join_ (Optional[set[str]]): A set of related tables to join with the query.
            order_ (Optional[dict]): A dictionary specifying the fields and their order (ASC/DESC).
            relations (Optional[list[str]]): A list of relationships to eagerly load with the query.

        Returns:
            ModelType | None: The first model instance that matches the query parameters, or None if no match is found.
        """
        query = await self._query(skip=skip, join_=join_, fields=fields, order_=order_, where_=where_)
        if relations:
            for relation in relations:
                query = query.options(selectinload(relation))
        query = await self.session.scalars(query)
        return query.first()

    @safeguard_db_ops()
    async def exists(
        self,
        where_: Optional[list] = None,
    ) -> bool:
        """Checks whether a model instance matching the given conditions exists.

        Args:
            where_ (Optional[list]): A list of conditions used to filter the records.

        Returns:
            bool: True if a model instance exists that matches the given conditions, False otherwise.
        """
        query = select(self.model_class)
        if where_:
            query = await self._query(where_=where_)
        result = await self.session.scalars(query)
        return bool(result.first())

    @safeguard_db_ops()
    async def delete(
        self,
        where_: Optional[list] = None,
        *,
        synchronize_session: SynchronizeSessionEnum = SynchronizeSessionEnum.FALSE,
    ):
        """Deletes model instances that match the given conditions.

        Args:
            where_ (Optional[list]): A list of conditions used to filter which model instances to delete.
            synchronize_session (SynchronizeSessionEnum): Defines how the session synchronization should be handled.
                Defaults to `SynchronizeSessionEnum.FALSE`.

        Returns:
            Sequence[ModelType]: A list of the deleted model instances.
        """
        del_instances = await self.get_many(where_=where_)
        query = delete(self.model_class)
        if where_ is not None:
            for condition in where_:
                query = query.where(condition)
        query = query.execution_options(synchronize_session=synchronize_session.value)
        await self.session.execute(query)
        return del_instances
