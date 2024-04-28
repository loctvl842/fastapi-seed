from functools import partial

from fastapi import Depends

from core.db import get_session
from core.utils import singleton
from machine.controllers import UserController
from machine.models import User
from machine.repositories import UserRepository


@singleton
class InternalProvider:
    """
    This provider provides controllers related to internal services.
    """

    # Repositories
    user_repository = partial(UserRepository, model=User)

    def get_user_controller(self, db_session=Depends(get_session)):
        return UserController(user_repository=self.user_repository(db_session=db_session))
