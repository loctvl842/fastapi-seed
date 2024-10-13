import asyncio
from contextlib import asynccontextmanager
from typing import TypeVar
from uuid import uuid4

from .session import Base, DBSessionKeeper

ModelType = TypeVar("ModelType", bound=Base)


@asynccontextmanager
async def session_context(db_session: DBSessionKeeper):
    """An asynchronous context manager that provides a transactional scope
    for database operations.

    Args:
        db_session (DBSession): The database session object that manages
        session lifecycle and transaction handling.
    """
    context = db_session.set_session_context(str(uuid4()))

    session_generator = db_session.get_session()
    session = None
    try:
        async for session in session_generator:
            yield session
    except asyncio.CancelledError:
        if session is not None:
            await session.rollback()
        raise
    except Exception:
        if session is not None:
            await session.rollback()
        raise
    finally:
        if session is not None:
            await session.remove()
        db_session.reset_session_context(context)
