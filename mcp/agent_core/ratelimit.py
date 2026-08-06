"""Rate limiting primitive shared by every agent (defence in depth, TASK R2).

A thin wrapper around `limits`' `MovingWindowRateLimiter` + in-memory storage — the
same strategy `slowapi` itself uses at the gateway (PLAN D3), for the one place
inside an MCP tool call that has no `Request` object to key a `slowapi.Limiter` on.
"""

from __future__ import annotations

import time

from limits import RateLimitItemPerMinute
from limits.storage import MemoryStorage
from limits.strategies import MovingWindowRateLimiter


class RateLimited(Exception):
    """A rate-limit bucket was exhausted.

    Typed, like `TurnTimeout` (master_orchestrator.services.orchestrator): the
    caller must tell it from any other failure so it can map to a retryable 429
    rather than a generic error.
    """

    def __init__(self, retry_after_s: float) -> None:
        self.retry_after_s = retry_after_s
        super().__init__(f"rate limit exceeded, retry after {retry_after_s:g}s")


class RateLimiter:
    """One in-memory moving-window rate-limit bucket, keyed at call time.

    The limit's amount (requests per minute) is read fresh on every call rather
    than baked in at construction, so a live config read (or a test's monkeypatch)
    is authoritative on the hot path. The moving-window storage is what persists
    across calls — the thing that actually needs to survive between hits — so a
    changing rpm never loses counts made under an unrelated bucket.

    `rpm <= 0` disables the bucket at the call site: `hit` always admits and never
    touches storage (PLAN D6/RK6 — a disabled bucket costs nothing on the hot path).
    """

    def __init__(self) -> None:
        self._limiter = MovingWindowRateLimiter(MemoryStorage())

    def hit(self, key: str, rpm: int) -> bool:
        """Consume one hit from the ``key`` bucket at ``rpm`` requests/minute.

        Returns True if the hit was admitted (or the bucket is disabled).
        """
        if rpm <= 0:
            return True
        return self._limiter.hit(RateLimitItemPerMinute(rpm), key)

    def retry_after_s(self, key: str, rpm: int) -> float:
        """Seconds until the ``key`` bucket has room again (minimum 1)."""
        if rpm <= 0:
            return 1.0
        reset_at, _ = self._limiter.get_window_stats(RateLimitItemPerMinute(rpm), key)
        return max(1.0, reset_at - time.time())
