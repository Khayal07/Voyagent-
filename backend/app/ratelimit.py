"""Sadə sliding-window rate limiter — tək server üçün in-memory.

Auth endpoint-ləri brute-force-dan, trip yaradılması LLM xərcindən qorunur.
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

_registry: list["RateLimiter"] = []


class RateLimiter:
    def __init__(self, limit: int, window_s: int):
        self.limit = limit
        self.window = window_s
        self._hits: dict[str, deque] = defaultdict(deque)
        _registry.append(self)

    def check(self, key: str) -> None:
        now = time.monotonic()
        dq = self._hits[key]
        while dq and now - dq[0] > self.window:
            dq.popleft()
        if len(dq) >= self.limit:
            raise HTTPException(
                status_code=429,
                detail="Həddindən çox sorğu — bir az sonra yenidən cəhd et",
                headers={"Retry-After": str(self.window)},
            )
        dq.append(now)

    def reset(self) -> None:
        self._hits.clear()


def reset_all() -> None:
    """Testlər arasında vəziyyəti təmizləmək üçün."""
    for rl in _registry:
        rl.reset()


def client_ip(request: Request) -> str:
    # Reverse-proxy arxasında real IP X-Forwarded-For-un ilk elementindədir
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


# Limitlər: auth IP başına, trip yaradılması istifadəçi başına, share IP başına
auth_limiter = RateLimiter(limit=10, window_s=300)
trip_limiter = RateLimiter(limit=10, window_s=3600)
share_limiter = RateLimiter(limit=30, window_s=60)


def limit_auth(request: Request) -> None:
    auth_limiter.check(client_ip(request))


def limit_share(request: Request) -> None:
    share_limiter.check(client_ip(request))
