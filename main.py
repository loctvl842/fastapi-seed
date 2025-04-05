import uvicorn
from fastapi import FastAPI

from contextlib import asynccontextmanager
from prometheus_client import make_asgi_app

from routes import main
from server.env import env
from server.config import AppConfigurer
from server.constants import ROOT_DIR


@asynccontextmanager
async def main_lifespan(app: FastAPI):
    yield


async def tool_lifespan(app: FastAPI):
    yield


def setup_applications() -> list[FastAPI]:
    """Create and configure all applications.

    Returns:
        List[FastAPI]: List of configured applications
    """
    main_app = FastAPI(
        title="<APP> API",
        description="<DESCRIPTION> API",
        version="0.0.1",
        root_path="/api",
        docs_url=None,
        redoc_url=None,
        lifespan=main_lifespan,
    )
    main_app.include_router(main.router)

    metric_app = make_asgi_app()
    main_app.mount("/metrics", metric_app)

    # Configure all apps
    applications = [main_app]
    for app in applications:
        configurer = AppConfigurer(app)
        configurer.setup_all()

    return applications


applications = setup_applications()
server = applications[0]

if __name__ == "__main__":
    uvicorn.run(
        "main:server",
        host=env.API_HOST,
        port=env.API_PORT,
        reload=env.API_DEBUG,
        reload_includes=[ROOT_DIR],
    )
