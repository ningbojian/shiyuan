from __future__ import annotations

from django.core.cache import cache


def cache_key(scope: str, identity: str) -> str:
    return f"throttle:{scope}:{identity}"


def is_limited(key: str, limit: int) -> bool:
    return cache.get(key, 0) >= limit


def record_failure(key: str, window: int) -> int:
    count = cache.get(key, 0) + 1
    cache.set(key, count, window)
    return count


def clear(key: str) -> None:
    cache.delete(key)


def rate_limit(key: str, limit: int, window: int) -> bool:
    """Return True and count one hit when under the limit; False when limited."""
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, window)
    return True
