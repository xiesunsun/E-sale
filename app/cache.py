import os

from redis import Redis
from redis.exceptions import RedisError

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
    try:
        _cache.ping()
        print("REDIS CONNECTED")
    except RedisError as e:
        print("REDIS CONNECTION ERROR:", e)


def close_cache() -> None:
    global _cache

    if _cache is not None:
        _cache.close()
        _cache = None


def get_cache() -> Redis:
    if _cache is None:
        raise RuntimeError("Cache is not initialized")

    return _cache


_RELEASE_LOCK_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def release_lock(
    lock_key: str,
    lock_token: str,
) -> bool:
    cache = get_cache()
    try:
        result = cache.eval(
            _RELEASE_LOCK_SCRIPT,
            1,
            lock_key,
            lock_token,
        )
        return result == 1
    except RedisError as e:
        print("REDIS ERROR:", e)
        return False
