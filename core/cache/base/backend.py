from abc import ABC, abstractmethod
from typing import Any


class BaseBackend(ABC):
    @abstractmethod
    async def get_(self, key: str) -> Any: ...

    @abstractmethod
    async def set_(self, key: str, value: Any, ttl: int = 60) -> None: ...

    @abstractmethod
    async def delete_startswith(self, value: str) -> None: ...
