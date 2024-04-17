import inspect
from typing import Callable

from .base import BaseKeyMaker


class DefaultKeyMaker(BaseKeyMaker):
    async def make(self, fn: Callable, prefix: str, args: tuple, kwargs: dict) -> str:
        path: str = f"{prefix}:{inspect.getmodule(fn).__name__}.{fn.__name__}"
        params: str = ""

        for param in inspect.signature(fn).parameters.values():
            params += f"{param.name}={kwargs.get(param.name)}:"

        if params:
            return f"{path}:{params[:-1]}"

        return path
