from uuid import uuid4

from starlette.types import ASGIApp, Receive, Scope, Send

from core.db.session import DB_MANAGER, Dialect


class SQLAlchemyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        db_session_handler = DB_MANAGER[Dialect.POSTGRES]
        session_id = str(uuid4())
        context = db_session_handler.set_session_context(session_id=session_id)

        try:
            await self.app(scope, receive, send)
        except Exception as e:
            raise e
        finally:
            await db_session_handler.session.remove()
            db_session_handler.reset_session_context(context=context)
