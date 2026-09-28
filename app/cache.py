import os

from redis import Redis

_cache: Redis | None = None


def open_cache() -> None:
    global _cache

    url = os.getenv(
        "ESALE_REDIS_URL",
        "redis://127.0.0.1:6379/0",
    )

    _cache = Redis.from_url(
        url,
        decode_responses=True,
    )

    _cache.ping()


def close_cache() -> None:
    global _cache

    if _cache is not None:
        _cache.close()
        _cache = None


def get_cache() -> Redis:
    if _cache is None:
        raise RuntimeError("Cache is not initialized")

    return _cache
