from core.controller import BaseController
from machine.models import User
from machine.repositories import UserRepository


class UserController(BaseController[User]):
    def __init__(self, user_repository: UserRepository):
        super().__init__(model_class=User, repository=user_repository)
        self.user_repository = user_repository
