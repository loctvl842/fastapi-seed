import logging

from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.cache import Cache, DefaultKeyMaker, RedisBackend
from core.exceptions import CustomException
from core.fastapi.middlewares import SQLAlchemyMiddleware
from core.response import Error
from core.settings import settings
from machine.api import router


def init_routers(app_: FastAPI) -> None:
    app_.include_router(router)


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.code,
            content=Error(error_code=exc.error_code, message=exc.message).model_dump(),
        )

    @app_.exception_handler(Exception)
    async def exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=Error(error_code=500, message="Internal Server Error").model_dump(),
        )


def init_cache() -> None:
    Cache.configure(backend=RedisBackend(), key_maker=DefaultKeyMaker())


def make_middleware() -> list[Middleware]:
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(SQLAlchemyMiddleware),
    ]
    return middleware


def create_machine() -> FastAPI:
    app_ = FastAPI(
        title="Trading Logic",
        description="Trading Logic API",
        version="0.0.1",
        docs_url=None if settings.ENV == "production" else "/docs",
        redoc_url=None if settings.ENV == "production" else "/redoc",
        middleware=make_middleware(),
    )
    app_.settings = settings
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    init_routers(app_)
    init_listeners(app_=app_)
    init_cache()
    return app_


machine = create_machine()
