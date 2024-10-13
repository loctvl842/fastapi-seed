import re

import toml
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

import core.utils as ut
from machine.api.ping import router as ping_router
from machine.api.v1 import router as router_v1
from machine.api.v2 import router as router_v2

router = APIRouter()
router.include_router(ping_router)
router.include_router(router_v1)
router.include_router(router_v2)
templates = Jinja2Templates(directory="templates")


@router.get("/")
def root(request: Request):
    with open("pyproject.toml", "r") as f:
        toml_content = f.read()

    toml_data = toml.loads(toml_content)
    project_name = ut.dig(toml_data, "tool.poetry.name", "fastAPI_project")
    project_name = re.sub(r"[-_]", " ", project_name).title()
    authors = ut.dig(toml_data, "tool.poetry.authors", [])

    context = {"project_name": project_name, "authors": authors}

    return templates.TemplateResponse("index.html", {"request": request, **context})


__all__ = ["router"]
