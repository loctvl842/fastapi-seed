from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/ping")
async def ping():
    return {"ping": "pong!"}
