# app/services/rate_limiter.py

from fastapi import HTTPException, Request
from typing import Dict, Tuple
import time
from datetime import datetime
import asyncio
from collections import defaultdict


class RateLimiter:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self._cleanup_lock = asyncio.Lock()

    async def check_rate_limit(self, request: Request) -> None:
        """
        Check if request is within rate limit.
        Raises HTTPException if rate limit is exceeded.
        """
        key = await self._get_key(request)
        allowed, retry_after = await self._is_allowed(key)

        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={"Retry-After": str(retry_after)}
            )

    async def _get_key(self, request: Request) -> str:
        """Get rate limit key from request."""
        # Default to IP address
        key = request.client.host

        # If authenticated, use user ID
        if hasattr(request.state, "user"):
            key = f"user_{request.state.user.id}"

        return f"{key}_{request.url.path}"

    async def _is_allowed(self, key: str) -> Tuple[bool, int]:
        """Check if request is allowed based on rate limiting."""
        now = time.time()
        minute_ago = now - 60

        async with self._cleanup_lock:
            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > minute_ago
            ]

            # Check rate limit
            if len(self.requests[key]) >= self.requests_per_minute:
                retry_after = int(60 - (now - self.requests[key][0]))
                return False, retry_after

            # Add new request
            self.requests[key].append(now)
            return True, 0

    async def cleanup(self):
        """Clean up old rate limit data."""
        async with self._cleanup_lock:
            now = time.time()
            minute_ago = now - 60

            for key in list(self.requests.keys()):
                self.requests[key] = [
                    req_time for req_time in self.requests[key]
                    if req_time > minute_ago
                ]

                if not self.requests[key]:
                    del self.requests[key]


# Create singleton instance
rate_limiter = RateLimiter()