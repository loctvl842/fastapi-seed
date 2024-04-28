from machine.models import User
from core.repository import BaseRepository


class UserRepository(BaseRepository[User]): ...
