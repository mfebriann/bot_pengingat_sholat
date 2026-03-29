"""
Redis cache layer for prayer times.

Key format: prayer:{city}:{date}  (date = YYYY-MM-DD)
TTL: 24 hours
"""

import json
import redis

from config.settings import settings
from utils.logger import setup_logger

logger = setup_logger("services.cache")

# Synchronous Redis client (used by Celery workers)
_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Get or create a Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
        )
    return _redis_client


def _make_key(city: str, date: str) -> str:
    """Build the Redis key for a city + date."""
    return f"prayer:{city.lower().strip()}:{date}"


def get_cached_prayer_times(city: str, date: str) -> dict[str, str] | None:
    """
    Retrieve cached prayer times for a city and date.

    Args:
        city: City name.
        date: Date in YYYY-MM-DD format.

    Returns:
        Dict of prayer times or None if cache miss.
    """
    try:
        r = get_redis()
        key = _make_key(city, date)
        data = r.get(key)
        if data:
            logger.debug("Cache HIT for %s", key)
            return json.loads(data)
        logger.debug("Cache MISS for %s", key)
        return None
    except redis.RedisError as e:
        logger.error("Redis error on GET %s: %s", city, e)
        return None


def set_cached_prayer_times(city: str, date: str, times: dict[str, str]) -> bool:
    """
    Store prayer times in Redis cache with 24-hour TTL.

    Args:
        city: City name.
        date: Date in YYYY-MM-DD format.
        times: Dict of prayer name → time string.

    Returns:
        True if cached successfully.
    """
    try:
        r = get_redis()
        key = _make_key(city, date)
        r.setex(key, settings.CACHE_TTL, json.dumps(times))
        logger.debug("Cache SET for %s (TTL=%ds)", key, settings.CACHE_TTL)
        return True
    except redis.RedisError as e:
        logger.error("Redis error on SET %s: %s", city, e)
        return False


def acquire_lock(lock_name: str, timeout: int = 300) -> redis.lock.Lock | None:
    """
    Acquire a Redis distributed lock to prevent duplicate scheduling.

    Args:
        lock_name: Unique name for the lock.
        timeout: Lock auto-release timeout in seconds.

    Returns:
        Lock object if acquired, None on failure.
    """
    try:
        r = get_redis()
        lock = r.lock(f"lock:{lock_name}", timeout=timeout)
        if lock.acquire(blocking=False):
            logger.debug("Lock acquired: %s", lock_name)
            return lock
        logger.debug("Lock already held: %s", lock_name)
        return None
    except redis.RedisError as e:
        logger.error("Redis lock error for %s: %s", lock_name, e)
        return None


def release_lock(lock: redis.lock.Lock) -> None:
    """Release a previously acquired Redis lock."""
    try:
        lock.release()
    except redis.RedisError as e:
        logger.error("Error releasing lock: %s", e)
