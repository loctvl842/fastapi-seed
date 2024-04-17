import pickle
from typing import Any

import redis
import ujson

from core.settings import settings

from .base import BaseBackend


class RedisBackend(BaseBackend):
    def __init__(self):
        # Redis client bound to pool of connections (auto-reconnecting).
        self.redis = redis.from_url(settings.REDIS_URL)

    async def get_(self, key: str) -> Any:
        response = self.redis.get(key)
        if not response:
            return
        try:
            return ujson.loads(response.decode("utf8"))
        except UnicodeDecodeError:
            return pickle.loads(response)

    async def set_(self, key: str, value: Any, ttl: int = 60) -> None:
        if isinstance(value, dict):
            value = ujson.dumps(value)
        elif isinstance(value, object):
            value = pickle.dumps(value)
        self.redis.set(key, value, ex=ttl)

    async def delete_startswith(self, value: str):
        for k in self.redis.scan_iter(f"{value}*"):
            self.redis.delete(k)
