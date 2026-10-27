import time
from typing import Any, Awaitable, Callable

class TTLCache:
    def __init__(self):
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str):
        item = self._data.get(key)
        if item is None:
            return None
        expires, value = item
        if expires < time.monotonic():
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        self._data[key] = (time.monotonic() + ttl, value)

    async def get_or_fetch(self, key: str, ttl: int, fetch: Callable[[], Awaitable[Any]]):
        cached = self.get(key)
        if cached is not None:
            return cached
        value = await fetch()
        self.set(key, value, ttl)
        return value

cache = TTLCache()