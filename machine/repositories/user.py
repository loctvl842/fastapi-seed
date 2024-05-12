from core.repository import BaseRepository
from machine.models import User


class UserRepository(BaseRepository[User]): ...
