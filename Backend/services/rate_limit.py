"""Lightweight in-memory rate limiting for high-risk endpoints."""

from collections import defaultdict, deque
from threading import Lock
from time import time
from typing import Optional


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, scope: str, key: str, limit: int, window_seconds: int) -> Optional[int]:
        now = time()
        bucket_key = f"{scope}:{key}"
        with self._lock:
            bucket = self._events[bucket_key]
            while bucket and now - bucket[0] > window_seconds:
                bucket.popleft()
            if len(bucket) >= limit:
                retry_after = int(window_seconds - (now - bucket[0]))
                return max(retry_after, 1)
            bucket.append(now)
        return None


rate_limiter = InMemoryRateLimiter()
