from abc import ABC, abstractmethod
from typing import Callable


class BaseKeyMaker(ABC):
    @abstractmethod
    async def make(self, fn: Callable, prefix: str, args: tuple, kwargs: dict) -> str: ...
