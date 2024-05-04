from typing import List

from fastapi import APIRouter, Depends

from machine.controllers import UserController
from machine.models import User
from machine.providers import InternalProvider
from machine.schemas.requests.user import UserRequest
from machine.schemas.responses.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create(
    body: UserRequest,
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    Create a new user

    Args:
    - **name**: User name
    """
    return await user_controller.create(body.model_dump())


@router.get("/", response_model=List[UserResponse])
async def list(
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    List all users
    """
    users = await user_controller.get_all()
    return users


@router.delete("/{id}")
async def delete(
    id: int,
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    Delete a user
    """
    return await user_controller.delete_many(where_=[User.id == id])
