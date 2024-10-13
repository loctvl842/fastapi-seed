from typing import List, Union

from fastapi import APIRouter, Depends, Query

from core.exceptions import BadRequestException
from machine.controllers import UserController
from machine.models import User
from machine.providers import InternalProvider
from machine.schemas.requests.user import UserRequest
from machine.schemas.responses.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=Union[UserResponse, List[UserResponse]])
async def create(
    body: Union[UserRequest, List[UserRequest]],
    bulk: bool = Query(False, description="Whether to create a bulk of users"),
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    Create user(s)
    """
    if bulk:
        if not isinstance(body, List):
            raise BadRequestException("Body must be a list when bulk is True")
        created_users = await user_controller.create_many([user.model_dump() for user in body])
        return created_users
    else:
        if isinstance(body, List):
            raise BadRequestException("Body must be a single user when bulk is False")
        created_user = await user_controller.create(body.model_dump())
        return created_user


@router.post("/upsert")
async def upsert(
    body: Union[UserRequest, List[UserRequest]],
    bulk: bool = Query(False, description="Whether to upsert a bulk of users"),
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    Upsert user(s)
    """
    if bulk:
        if not isinstance(body, List):
            raise BadRequestException("Body must be a list when bulk is True")
        created_users = await user_controller.upsert_many(index_elements=["id"], attributes_list=[user.model_dump() for user in body])
        return created_users
    else:
        if isinstance(body, List):
            raise BadRequestException("Body must be a single user when bulk is False")
        created_user = await user_controller.upsert(index_elements=["id"], attributes=body.model_dump())
        return created_user


@router.get("/")
async def list(
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    List all users
    """
    users = await user_controller.get_many(distinct=[User.name])
    return users


@router.delete("/{id}")
async def delete(
    id: int,
    user_controller: UserController = Depends(InternalProvider().get_user_controller),
):
    """
    Delete a user
    """
    return await user_controller.delete(where_=[User.id == id])
