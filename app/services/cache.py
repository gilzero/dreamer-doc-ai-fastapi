# app/services/cache.py

from typing import Any, Optional, Union
import json
from datetime import timedelta
import pickle
import hashlib
import logging
from redis import asyncio as aioredis
from fastapi import Request
from functools import wraps

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        self.binary_redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding=None,
            decode_responses=False
        )

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache."""
        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Cache get error: {str(e)}")
            return None

    async def set(
            self,
            key: str,
            value: str,
            expire: Optional[int] = None
    ) -> bool:
        """Set value in cache with optional expiration."""
        try:
            await self.redis.set(key, value, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {str(e)}")
            return False

    async def get_object(self, key: str) -> Optional[Any]:
        """Get Python object from cache."""
        try:
            data = await self.binary_redis.get(key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"Cache get_object error: {str(e)}")
            return None

    async def set_object(
            self,
            key: str,
            value: Any,
            expire: Optional[int] = None
    ) -> bool:
        """Set Python object in cache with optional expiration."""
        try:
            data = pickle.dumps(value)
            await self.binary_redis.set(key, data, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Cache set_object error: {str(e)}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    async def clear_pattern(self, pattern: str) -> bool:
        """Clear all keys matching pattern."""
        try:
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match=pattern)
                if keys:
                    await self.redis.delete(*keys)
                if cursor == 0:
                    break
            return True
        except Exception as e:
            logger.error(f"Cache clear_pattern error: {str(e)}")
            return False


# Create singleton instance
cache = CacheService()


def cache_response(
        expire: int = 300,
        key_prefix: str = "",
        include_user: bool = False
):
    """
    Decorator to cache API responses.

    Args:
        expire: Cache expiration time in seconds
        key_prefix: Prefix for cache key
        include_user: Whether to include user ID in cache key
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request object
            request = next((arg for arg in args if isinstance(arg, Request)), None)
            if not request:
                return await func(*args, **kwargs)

            # Generate cache key
            key_parts = [key_prefix, request.url.path]

            # Add query params to key
            if request.query_params:
                key_parts.append(str(request.query_params))

            # Add user ID to key if required
            if include_user and hasattr(request.state, "user"):
                key_parts.append(str(request.state.user.id))

            cache_key = hashlib.md5(
                "_".join(key_parts).encode()
            ).hexdigest()

            # Try to get from cache
            cached_response = await cache.get(cache_key)
            if cached_response:
                return json.loads(cached_response)

            # Execute function and cache result
            response = await func(*args, **kwargs)
            await cache.set(
                cache_key,
                json.dumps(response),
                expire=expire
            )

            return response

        return wrapper

    return decorator


def clear_cache_pattern(pattern: str):
    """
    Decorator to clear cache patterns after function execution.
    Useful for mutations that invalidate cached data.
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            await cache.clear_pattern(pattern)
            return response

        return wrapper

    return decorator