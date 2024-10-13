from functools import wraps
from typing import Awaitable, Callable, TypeVar
from uuid import uuid4

from typing_extensions import ParamSpec

from core.settings import settings

from .session import DB_MANAGER, Dialect

P = ParamSpec("P")
R = TypeVar("R")


class Transactional:
    def __call__(
        self, fn: Callable[P, Awaitable[R]], *, dialect: Dialect = Dialect.POSTGRES
    ) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def _transactional(*args: P.args, **kwargs: P.kwargs) -> R:
            # Unit testing does not involve database connections.
            if settings.PYTEST_UNIT:
                return await fn(*args, **kwargs)
            db_session_keeper = DB_MANAGER[dialect]

            try:
                result = await fn(*args, **kwargs)
                await db_session_keeper.session.commit()
            except Exception as e:
                await db_session_keeper.session.rollback()
                raise e

            return result

        return _transactional


def session_scope(dialect: Dialect):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            db_session_keeper = DB_MANAGER[dialect]
            session_id = str(uuid4())
            context = db_session_keeper.set_session_context(session_id=session_id)
            try:
                return await fn(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                await db_session_keeper.session.remove()
                db_session_keeper.reset_session_context(context=context)

        return wrapper

    return decorator
