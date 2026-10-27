import asyncio
import logging
import aiohttp

logger = logging.getLogger(__name__)

class ServiceUnavailable(Exception):
    """Внешний сервис недоступке после всех попыток."""

def _is_permanent(exc: Exception) -> bool:
    return(
        isinstance(exc, aiohttp.ClientResponseError)
        and 400 <= exc.status < 500
        and exc.status != 429
    )

async def with_retry(fn, *, name: str, attempts: int = 3, base_delay: float = 0.5):
    for attempt in range(1, attempts + 1):
        try:
            return await fn()
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            if _is_permanent(exc):
                logger.error("%s: постоянная ошибка запроса, статус %s", name, exc.status)
                raise ServiceUnavailable(name) from exc
            logger.warning("%s: попытка %d/%d не удалась: %s", name, attempt, attempts, type(exc).__name__)
            if attempt < attempts:
                await asyncio.sleep(base_delay * 2 ** (attempt - 1))
    raise ServiceUnavailable(name)