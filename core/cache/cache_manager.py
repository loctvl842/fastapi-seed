from functools import wraps
from typing import Callable, TypeVar

import core.utils as ut
from core.utils.decorators import stopwatch

from .base import BaseBackend, BaseKeyMaker

T = TypeVar("T")


class CacheManager:
    def __init__(self):
        self.backend: BaseBackend = None
        self.key_maker: BaseKeyMaker = None

    def configure(self, backend: BaseBackend, key_maker: BaseKeyMaker):
        self.backend = backend
        self.key_maker = key_maker

    @stopwatch(prefix="cache")
    async def attempt(self, key: str, ttl: int, fn: Callable[..., T], *args, **kwargs) -> T | None:
        be = self.backend
        ttl = ttl or 60

        if not be:
            raise ValueError("Backend not initialized")

        cached_response = await be.get_(key)
        if cached_response is not None:
            return cached_response

        response = await ut.attempt(fn, *args, **kwargs)
        is_error = ut.is_error(response)
        await be.set_(key=key, value=response if not is_error else None, ttl=ttl)

        if is_error:
            raise response

        return response if not isinstance(response, Exception) else None

    def cached(self, prefix: str = None, ttl: int = 60, key_maker: BaseKeyMaker = None):
        def _cached(fn):
            @wraps(fn)
            async def __cached(*args, **kwargs):
                be = self.backend
                km = key_maker or self.key_maker

                if not be or not km:
                    raise ValueError("Backend or KeyMaker not initialized")

                key = await km.make(fn=fn, prefix=prefix, args=args, kwargs=kwargs)

                response = await self.attempt(key, ttl, fn, *args, **kwargs)

                return response

            return __cached

        return _cached


Cache = CacheManager()
