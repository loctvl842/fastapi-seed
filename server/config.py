"""FastAPI application initialization and configuration module.

This module provides utility functions for setting up a FastAPI application with
documentation, error handlers, and middleware. It includes functionality for Swagger UI,
ReDoc, custom error handling, and CORS configuration.
"""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError, ResponseValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.routing import Mount
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import toml
from pathlib import Path

from .types import Error
from .constants import STATIC_DIR, TEMPLATES_DIR
from .exceptions import APIException


class AppConfigurer:
    """Handles FastAPI application configuration and setup.

    This class encapsulates the logic for initializing documentation, error handlers,
    and middleware for a FastAPI application.

    Attributes:
        app (FastAPI): The FastAPI application instance to configure.
        _cached_authors (Optional[List[str]]): Cached list of project authors from pyproject.toml.
    """

    def __init__(self, app: FastAPI):
        self.app = app
        self._cached_authors = None
        self._templates = Jinja2Templates(directory=TEMPLATES_DIR)

    def setup_all(self) -> None:
        """Configure all aspects of the FastAPI application.

        This method initializes documentation, error handlers, and middleware
        in a single call.
        """
        self.init_docs()
        self.init_exception_handler()
        self.init_middlewares()

    def init_docs(self) -> None:
        """Initialize API documentation endpoints.

        Sets up Swagger UI and ReDoc documentation, static file serving,
        and the root page template.
        """
        self.app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
        self._setup_swagger_ui()
        self._setup_redoc()
        self._setup_root_page()

    def _setup_swagger_ui(self) -> None:
        """Configure Swagger UI documentation endpoint."""

        @self.app.get("/docs", include_in_schema=False)
        async def swagger_ui_html(req: Request) -> HTMLResponse:
            root_path = req.scope.get("root_path", "").rstrip("/")
            openapi_url = root_path + self.app.openapi_url
            oauth2_redirect_url = self.app.swagger_ui_oauth2_redirect_url
            if oauth2_redirect_url:
                oauth2_redirect_url = root_path + oauth2_redirect_url

            return get_swagger_ui_html(
                openapi_url=openapi_url,
                title=f"{self.app.title} - Swagger UI",
                oauth2_redirect_url=oauth2_redirect_url,
                init_oauth=self.app.swagger_ui_init_oauth,
                swagger_favicon_url=f"{self.app.root_path}/static/favicon.svg",
                swagger_ui_parameters=self.app.swagger_ui_parameters,
            )

    def _setup_redoc(self) -> None:
        """Configure ReDoc documentation endpoint."""

        @self.app.get("/redoc", include_in_schema=False)
        async def redoc_html(req: Request) -> HTMLResponse:
            root_path = req.scope.get("root_path", "").rstrip("/")
            openapi_url = root_path + self.app.openapi_url
            return get_redoc_html(
                openapi_url=openapi_url,
                title=f"{self.app.title} - ReDoc",
                redoc_favicon_url=f"{self.app.root_path}/static/favicon.svg",
            )

    def _get_authors(self) -> list[str]:
        """Retrieve project authors from pyproject.toml.

        Returns:
            List[str]: List of project authors.
        """
        if self._cached_authors is None:
            pyproject_path = Path("pyproject.toml")
            if pyproject_path.is_file():
                with open(pyproject_path, "r") as f:
                    toml_data = toml.loads(f.read())
                self._cached_authors = (
                    toml_data.get("tool", {}).get("poetry", {}).get("authors", ["loctvl842 <loclepnvx@gmail.com>"])
                )
            else:
                self._cached_authors = []
        return self._cached_authors

    def _setup_root_page(self) -> None:
        """Configure the root page endpoint with template rendering."""

        @self.app.get("/")
        def root(request: Request):
            sub_apps = [
                route.app for route in self.app.routes if isinstance(route, Mount) and isinstance(route.app, FastAPI)
            ]

            context = {
                "project_name": self.app.title,
                "authors": self._get_authors(),
                "root_path": self.app.root_path,
                "sub_apps": sub_apps,
            }

            return self._templates.TemplateResponse("index.html", {"request": request, **context})

    def init_exception_handler(self) -> None:
        """Initialize error handlers for various exception types."""

        # Validation
        @self.app.exception_handler(RequestValidationError)
        async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
            return JSONResponse(
                status_code=422,
                content=Error(
                    error_code=422,
                    message="Request validation failed",
                    detail=str(exc),
                ).model_dump(exclude_none=True),
            )

        @self.app.exception_handler(ResponseValidationError)
        async def response_validation_exception_handler(request: Request, exc: ResponseValidationError):
            return JSONResponse(
                status_code=422,
                content=Error(
                    error_code=422,
                    message="Response validation failed",
                    detail=str(exc),
                ).model_dump(exclude_none=True),
            )

        @self.app.exception_handler(APIException)
        async def api_exception_handler(request: Request, exc: APIException):
            return JSONResponse(
                status_code=exc.code,
                content=Error(error_code=exc.error_code, message=exc.message, detail=exc.detail).model_dump(
                    exclude_none=True
                ),
                headers=exc.headers,
            )

        @self.app.exception_handler(Exception)
        async def exception_handler(request: Request, exc: Exception):
            return JSONResponse(
                status_code=500,
                content=Error(error_code=500, message="Internal Server Error").model_dump(exclude_none=True),
            )

    def init_middlewares(self) -> None:
        """Initialize CORS and other middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
