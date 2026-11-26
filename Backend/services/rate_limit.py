"""
ImpactAI — Centralized rate limiting service.

Provides configurable per-IP and per-user rate limiting using a sliding
token-window algorithm. Designed to operate safely in memory for local development
and testing, with extensible architecture for distributed Redis backing in multi-instance deployments.
"""

from collections import defaultdict, deque
import logging
import os
from threading import Lock
from time import time
from typing import Optional

from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Configurable Default Policies
DEFAULT_LIMITS = {
    "login_ip": (int(os.getenv("RATE_LIMIT_LOGIN_IP", "10")), 60),
    "login_email": (int(os.getenv("RATE_LIMIT_LOGIN_EMAIL", "5")), 60),
    "signup_ip": (int(os.getenv("RATE_LIMIT_SIGNUP_IP", "5")), 60),
    "signup_email": (int(os.getenv("RATE_LIMIT_SIGNUP_EMAIL", "3")), 60),
    "anonymous_session": (int(os.getenv("RATE_LIMIT_ANON_SESSION", "10")), 3600),
    "chat_user": (int(os.getenv("RATE_LIMIT_CHAT_USER", "20")), 60),
    "chat_daily": (int(os.getenv("RATE_LIMIT_CHAT_DAILY", "200")), 86400),
    "mood_user": (int(os.getenv("RATE_LIMIT_MOOD_USER", "30")), 60),
    "analytics_user": (int(os.getenv("RATE_LIMIT_ANALYTICS_USER", "40")), 60),
}


class SlidingWindowRateLimiter:
    """Sliding-window rate limiter with thread-safe bucket locking."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, scope: str, key: str, limit: int, window_seconds: int) -> Optional[int]:
        now = time()
        bucket_key = f"{scope}:{key}"
        with self._lock:
            bucket = self._events[bucket_key]
            # Evict timestamps older than the sliding window
            while bucket and now - bucket[0] > window_seconds:
                bucket.popleft()

            if len(bucket) >= limit:
                retry_after = int(window_seconds - (now - bucket[0]))
                return max(retry_after, 1)

            bucket.append(now)
        return None

    def enforce(self, scope: str, key: str, limit: Optional[int] = None, window_seconds: Optional[int] = None) -> None:
        """Enforce rate limit; raises HTTP 429 with standard Retry-After header if exceeded."""
        if limit is None or window_seconds is None:
            default_limit, default_window = DEFAULT_LIMITS.get(scope, (30, 60))
            limit = limit or default_limit
            window_seconds = window_seconds or default_window

        retry_after = self.check(scope, key, limit, window_seconds)
        if retry_after:
            logger.warning("Rate limit exceeded for %s:%s (Retry-After: %ss)", scope, key, retry_after)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests for {scope}. Please try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )


rate_limiter = SlidingWindowRateLimiter()
