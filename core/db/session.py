from collections import deque
from contextvars import ContextVar, Token
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_scoped_session, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.sql.expression import Delete, Insert, Update

from core.settings import settings


class EngineType(Enum):
    WRITER = "writer"
    READER = "reader"


class RoutingSession(Session):
    def __init__(self, engines, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.engines = engines

    def get_bind(self, mapper=None, clause=None, **kw):
        if self._flushing or isinstance(clause, (Update, Delete, Insert)):
            return self.engines[EngineType.WRITER].sync_engine
        else:
            return self.engines[EngineType.READER].sync_engine


class DBSessionKeeper:
    def __init__(self, database_uri: str, testing=settings.PYTEST):
        self.session_context: ContextVar[str] = ContextVar(str(uuid4()))

        if not testing:
            self.engines = {
                EngineType.WRITER: create_async_engine(database_uri, pool_recycle=3600),
                EngineType.READER: create_async_engine(database_uri, pool_recycle=3600),
            }
        else:
            self.engines = {
                EngineType.WRITER: create_async_engine(database_uri, poolclass=NullPool),
                EngineType.READER: create_async_engine(database_uri, poolclass=NullPool),
            }

        self.async_session_factory = async_sessionmaker(
            class_=AsyncSession,
            sync_session_class=RoutingSession,
            expire_on_commit=False,
            engines=self.engines,
        )
        self._session = async_scoped_session(
            session_factory=self.async_session_factory,
            scopefunc=self.get_session_context,
        )

    @property
    def session(self) -> async_scoped_session[AsyncSession]:
        return self._session

    def get_session_context(self) -> str:
        return self.session_context.get()

    def set_session_context(self, session_id: str) -> Token:
        return self.session_context.set(session_id)

    def reset_session_context(self, context):
        self.session_context.reset(context)

    async def get_session(self):
        """
        Get database session
        """
        try:
            yield self.session
        finally:
            await self.session.close()


"""
All database sessions
"""


class Dialect(str, Enum):
    POSTGRES = "This is the main session of machine"
    AUTH_POSTGERS = "This DB Session served for OAuth2"


DB_MANAGER = {
    Dialect.POSTGRES: DBSessionKeeper(settings.SQLALCHEMY_POSTGRES_URI),
    Dialect.AUTH_POSTGERS: DBSessionKeeper(settings.SQLALCHEMY_POSTGRES_URI),
}


SEEN = "NOW YOU SEE ME!"


class Base(DeclarativeBase):
    """
    A base class for SQLAlchemy models, providing a method to convert model
    instances to dictionaries while excluding specified fields and preventing
    recursive loops.

    Attributes:
        __exclude__ (list): A list of field names to be excluded from the
            dictionary representation of the model instance.

    Methods:
        to_dict() -> Dict[str, Any]:
            Converts the model instance to a dictionary, excluding fields listed
            in the `__exclude__` attribute.
    """

    __exclude__ = []

    def to_dict(
        self,
        *,
        exclude: Optional[list[str]] = None,
        bfs: bool = True,
    ) -> dict[str, Any]:
        exclude = exclude or []
        exclude.extend(self.__exclude__ or [])
        if bfs:
            result = self._to_dict_bfs(exclude=exclude)
        else:
            result = self._to_dict_dfs(exclude=exclude)
        result = {k: v for k, v in result.items() if k not in exclude}
        return result

    def _to_dict_dfs(self, exclude: Optional[list[str]] = None, seen: set = None) -> dict[str, Any]:
        """
        Convert the SQLAlchemy model instance to a dictionary.
        """
        # Get the dictionary representation of the SQLAlchemy model instance
        if seen is None:
            seen = set()

        # Avoid infinite recursion by keeping track of seen objects
        if id(self) in seen:
            return SEEN

        seen.add(id(self))

        # Get the dictionary representation of the SQLAlchemy model instance
        obj_dict = self.__dict__

        # Filter out internal attributes and create a new dictionary
        filtered_obj_dict = {}
        for key, value in obj_dict.items():
            if key.startswith("_") or (exclude and key in exclude):
                continue
            if isinstance(value, Base):
                # Recursively convert the related object to a dictionary
                v = value._to_dict_dfs(seen=seen)
                if v is not SEEN:
                    filtered_obj_dict[key] = v
            elif isinstance(value, list):
                v = []
                for item in value:
                    if isinstance(item, Base):
                        x = item._to_dict_dfs(seen=seen)
                        if x is not SEEN:
                            v.append(x)
                    else:
                        v.append(item)
                # filtered_obj_dict[key] = [item._to_dict_dfs(seen=seen) if isinstance(item, Base) else item for item in value]
                filtered_obj_dict[key] = v
            else:
                filtered_obj_dict[key] = value

        return filtered_obj_dict

    def _to_dict_bfs(self, exclude: Optional[list[str]] = None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        queue: deque = deque([(self, result)])
        seen: set[int] = set()

        while queue:
            current_obj, current_dict = queue.popleft()
            obj_id = id(current_obj)

            if obj_id in seen:
                continue

            seen.add(obj_id)

            # Get the dictionary representation of the SQLAlchemy model instance
            obj_dict = current_obj.__dict__

            for key, value in obj_dict.items():
                if key.startswith("_") or (exclude and key in exclude):
                    continue

                if isinstance(value, Base):
                    if id(value) in seen:
                        # Then, omit key
                        continue
                    else:
                        # Then, initialize nested dictionary for related object
                        current_dict[key] = {}
                        queue.append((value, current_dict[key]))
                elif isinstance(value, list):
                    current_dict[key] = []
                    for item in value:
                        if isinstance(item, Base):
                            if id(item) in seen:
                                continue
                            else:
                                # Then, initialize nested dictionary for each related object in the list
                                item_dict: dict[str, Any] = {}
                                current_dict[key].append(item_dict)
                                queue.append((item, item_dict))
                        else:
                            current_dict[key].append(item)
                else:
                    current_dict[key] = value

        return result

