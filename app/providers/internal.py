from functools import partial

from fastapi import Depends

from app.controllers import UserController
from app.models import User
from app.repositories import UserRepository
from core.db import get_session
from core.utils import singleton


@singleton
class InternalProvider:
    """
    This provider provides controllers related to internal services.
    """

    # Repositories
    user_repository = partial(UserRepository, model=User)

    def get_user_controller(self, db_session=Depends(get_session)):
        return UserController(user_repository=self.user_repository(db_session=db_session))
