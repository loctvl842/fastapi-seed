import re
from contextlib import asynccontextmanager

import toml
from fastapi import FastAPI, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import core.utils as ut
from core.cache import Cache, DefaultKeyMaker, RedisBackend
from core.exceptions import CustomException
from core.fastapi.middlewares import SQLAlchemyMiddleware
from core.logger import syslog
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


def init_sentry() -> None:
    try:
        if ut.has("sentry_sdk"):
            import sentry_sdk

            sentry_sdk.init(
                dsn=settings.SENTRY_DSN,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0,
            )
    except Exception as e:
        syslog.error(f"Failed to initialize Sentry SDK: {e}")


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


def on_startup(app: FastAPI):
    """
    Executed before application starts taking requests, during the startup.
    """

    # Load logger
    import core.logger  # noqa: F401


def on_shutdown(app: FastAPI):
    """
    Executed after application finishes handling requests, right before the shutdown.
    """


@asynccontextmanager
async def lifespan(app: FastAPI):
    on_startup(app)
    yield
    on_shutdown(app)


def create_machine() -> FastAPI:
    with open("pyproject.toml", "r") as f:
        toml_content = f.read()

    toml_data = toml.loads(toml_content)
    project_name = ut.dig(toml_data, "tool.poetry.name", "fastAPI_project")
    project_name = re.sub(r"[-_]", " ", project_name).title()
    project_description = ut.dig(toml_data, "tool.poetry.description", "fastAPI_project")

    app_ = FastAPI(
        title=project_name,
        description=project_description,
        version="0.0.1",
        root_path="/api",
        docs_url="/docs",
        redoc_url="/redoc",
        middleware=make_middleware(),
        lifespan=lifespan,
    )
    app_.settings = settings
    init_routers(app_)
    init_listeners(app_=app_)
    init_cache()
    init_sentry()
    return app_


machine = create_machine()
