from fastapi import APIRouter

from .ping import router as ping_router

router = APIRouter()
router.include_router(ping_router)

__all__ = ["router"]
