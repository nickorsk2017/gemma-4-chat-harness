"""Gateway rate limiting: a `slowapi` Limiter over the `limits` package (R1, PLAN D1).

One module-level `Limiter`, keyed by remote address (`slowapi`'s default key func;
no proxy-header trust in this task — not required by R1). Registered in
`gateway/main.py` with THIS module's `rate_limit_exceeded_handler`, not slowapi's
own `_rate_limit_exceeded_handler` (RK1): the app's `ApiResponse.fail` envelope
must be what a 429 carries, never slowapi's default JSON shape.
"""

from __future__ import annotations

import time

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from _common.env import get_settings
from gateway.services.agent_client import RATE_LIMITED_CODE

# Keyed by remote address; the storage is `limits`' in-memory default (no Redis/
# Postgres — PLAN constraint), which is fine for the single-replica dev deployment
# R4 targets (RK5: N replicas would admit N x this, out of scope here).
limiter = Limiter(key_func=get_remote_address)


def default_limit_value() -> str:
    """The configured default limit string, read live from settings (R4/D6).

    A callable limit value (rather than a literal string baked in at decoration
    time) is what lets `GATEWAY_RATE_LIMIT_DEFAULT` be read fresh per request and
    what makes an empty string disable the gate: `limits.parse_many("")` raises
    `ValueError`, which slowapi's own dynamic-limit evaluation catches and treats
    as "no limit for this request" (RK6) — no extra branch on the hot path.
    """
    return get_settings().rate_limit_default


def _retry_after_seconds(request: Request) -> float:
    """Raw seconds until the limit just hit resets (not yet ceiled/floored).

    Reads the window slowapi already computed for the failed limit
    (`request.state.view_rate_limit`, set by `Limiter.__evaluate_limits` right
    before it raises). `_fail` (gateway/routers/chat.py) owns the ceiling and the
    minimum-1 floor — this only supplies the raw number.
    """
    current = getattr(request.state, "view_rate_limit", None)
    if not current:
        return 1.0
    item, identifiers = current
    try:
        reset_at, _ = limiter.limiter.get_window_stats(item, *identifiers)
    except Exception:  # noqa: BLE001 - header math must never break the 429 itself
        return 1.0
    return max(0.0, reset_at - time.time())


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Map a slowapi rejection onto the existing `ApiResponse.fail` envelope.

    Deferred import: `gateway.routers.chat` imports `limiter` from this module at
    definition time (for the `@limiter.limit(...)` decorators), so importing `_fail`
    back at module load would be circular. Both modules are fully loaded by the
    time a request actually triggers this handler.
    """
    from gateway.routers.chat import _fail

    return _fail(
        429,
        "rate limit exceeded",
        RATE_LIMITED_CODE,
        _retry_after_seconds(request),
    )
