# PLAN — 2026-08-05-rate-limit-gateway-orchestrator
plan_version: 1

## v1

### D1 — Gateway library binding (R1)
`slowapi` (Starlette/FastAPI middleware over the `limits` package) sits at the
gateway, the only layer with a real `Request` object. One module-level
`slowapi.Limiter` instance, keyed by `get_remote_address` (default; no proxy-header
trust in this task — not required by R1). Registered via
`slowapi.errors.RateLimitExceeded` exception handler, not the library's default
handler, so the 429 body matches the existing `ApiResponse.fail` envelope
(prerequisite for R3/A1) rather than slowapi's own JSON shape.

### D2 — Gateway scope (R1)
Decorated: `POST /api/chat`, `POST /api/chat/files` (the billable/stateful,
LLM-reaching surface named in R3). Not decorated: `DELETE /api/chat/threads/{id}`
(store-only, not billable — out of R1's surface) and `GET /api/health` (A2).
`slowapi.Limiter.limit(...)` requires the decorated function to accept a `Request`
parameter for key extraction; both handlers gain one (signature-only change, no
routing/contract change).

### D3 — Orchestrator library binding and key (R2)
No `Request` object exists inside an MCP tool call, so `slowapi` does not fit here;
this is exactly the gap R2 exists to cover. Bind `limits` directly:
`MovingWindowRateLimiter` over `MemoryStorage`, mirrored as a new `agent_core`
primitive (`agent_core/ratelimit.py`) alongside the existing `FilePayload` /
`AgentResponse` mirrors, since `master_orchestrator` is presently the only
consumer but any future agent needing R2-style defence inherits it for free.
Two `RateLimitItemPerMinute` checks per turn, both in `Orchestrator.run`:
1. per-`thread_id` (missing thread_id -> one shared anonymous bucket) — bounds one
   conversation;
2. process-global — bounds total spend from a caller that rotates thread_ids,
   reaching the orchestrator directly and bypassing the gateway's per-IP bucket
   (the scenario R2 names).

### D4 — Orchestrator check placement (R2, R3)
The check runs at the top of `Orchestrator.run`, before `asyncio.wait_for` wraps
`_run_turn` — earlier than `TurnTimeout`'s guard, so a rejected turn never starts
the budget clock, never calls `_files.validate`, `check_input`, or `store.load`
(R3: no LLM, no guardrails, no store read/write). A typed `RateLimited(retry_after_s)`
exception (mirrors `TurnTimeout`) crosses to `tools/start_job.py`, caught next to the
existing `TurnTimeout` catch, mapped to `AgentResponse.fail(AGENT, str(exc),
code=RATE_LIMITED_CODE, retry_after_s=exc.retry_after_s)` — meta is an open dict
already carrying `TURN_TIMEOUT_CODE` this way, so no envelope schema change.

### D5 — Rejection path to the wire (R3)
Two independent 429 sources, one gateway-side mapping:
- gateway's own `slowapi` rejection: caught by the D1 handler, answered 429 directly,
  agent never called.
- orchestrator's rejection: `RATE_LIMITED_CODE` mirrored in
  `gateway/services/agent_client.py` next to `TURN_TIMEOUT_CODE`; `AgentOutcome`
  gains `retry_after_s: float | None`, read from `meta.retry_after_s` in
  `_to_outcome`; `routers/chat.py:_reply` gains a branch beside the existing
  `TURN_TIMEOUT_CODE` -> 504 one, mapping `RATE_LIMITED_CODE` -> 429; `_fail` gains
  an optional `Retry-After` header parameter (ceiling to whole seconds, minimum 1)
  used by both the D1 handler and this branch, so one helper produces both 429s.

### D6 — Configuration (R4)
Gateway (`_common/env/settings.py`, `GATEWAY_` prefix): `rate_limit_default: str`
(slowapi limit-string syntax, e.g. `"30/minute"`; empty string disables). Orchestrator
(`master_orchestrator/config.py`, `ORCHESTRATOR_` prefix): `rate_limit_thread_rpm`,
`rate_limit_global_rpm` (both int; <=0 disables that bucket). Defaults sized for a
single-replica dev deployment, above ordinary single-browser use (mirrors the sizing
reasoning already present for `turn_budget_s`).

### D7 — Frontend (R5)
`ChatErrorCode` widens to `"turn_timeout" | "rate_limited"`; `toErrorCode` in
`chatService.ts` narrows both (currently only narrows `turn_timeout`). In the store,
`isTurnTimeout` generalizes to a retryable-code predicate covering both codes; the
existing placeholder + `retryable: true` + `pending` path is reused unchanged so a
429 gets the same retry affordance the timeout already has (A4) — no second
affordance introduced. `retry_after_s` is read from the outcome but not surfaced in
this task (no acceptance criterion asks for a countdown); explicit non-goal, not an
oversight.

### File-by-file
1. `backend/pyproject.toml` — add `slowapi` dependency.
2. `mcp/agent_core/pyproject.toml` — add `limits` dependency.
3. `backend/_common/env/settings.py` — `rate_limit_default` (D6).
4. `backend/gateway/services/ratelimit.py` (NEW) — the `Limiter` instance, key func,
   and the `RateLimitExceeded` -> `ApiResponse.fail` exception handler (D1).
5. `backend/gateway/main.py` — register the exception handler + `SlowAPIMiddleware`.
6. `backend/gateway/routers/chat.py` — `Request` param + `@limiter.limit(...)` on
   `/chat`, `/chat/files` (D2); `_fail` gains optional `Retry-After` header param;
   `_reply` gains the `RATE_LIMITED_CODE` -> 429 branch (D5).
7. `backend/gateway/services/agent_client.py` — `RATE_LIMITED_CODE`;
   `AgentOutcome.retry_after_s`; read `meta.retry_after_s` in `_to_outcome` (D5).
8. `mcp/agent_core/ratelimit.py` (NEW) — `RateLimited` exception + thin
   `MovingWindowRateLimiter`/`MemoryStorage` wrapper (D3).
9. `mcp/agent_core/__init__.py` — export `RateLimited` + the wrapper.
10. `mcp/master_orchestrator/config.py` — `rate_limit_thread_rpm`,
    `rate_limit_global_rpm` (D6).
11. `mcp/master_orchestrator/services/orchestrator.py` — `RATE_LIMITED_CODE`; the
    two checks at the top of `run` (D3, D4).
12. `mcp/master_orchestrator/tools/start_job.py` — catch `RateLimited` ->
    `AgentResponse.fail` with code + `retry_after_s` (D4).
13. `frontend/types/chat.d.ts` — widen `ChatErrorCode` (D7).
14. `frontend/services/chatService.ts` — `toErrorCode` narrows both codes (D7).
15. `frontend/stores/chatStore.ts` — retryable-code predicate generalization (D7).
16. `backend/tests/test_rate_limit.py` (NEW) — A1, A2.
17. `mcp/tests/test_rate_limit.py` (NEW) — A3, styled on `mcp/tests/test_turn_timeout.py`
    (monkeypatch the settings, assert `RateLimited` fires before `_run_turn` starts).
18. `frontend/__tests__/chatStore.test.ts` — A4 case appended.
19. `.env.example`, `backend/.env.example`, `mcp/.env.example` — document the new
    `GATEWAY_RATE_LIMIT_DEFAULT`, `ORCHESTRATOR_RATE_LIMIT_THREAD_RPM`,
    `ORCHESTRATOR_RATE_LIMIT_GLOBAL_RPM` knobs.

### Sequencing
P1 gateway: `ratelimit.py` + settings + `main.py` wiring + `chat.py` decorators;
   tests A1, A2.
P2 orchestrator: `agent_core/ratelimit.py` + settings + `orchestrator.py` checks +
   `start_job.py` mapping; test A3.
P3 gateway wire-through of the orchestrator's rejection: `agent_client.py`
   `retry_after_s` + `chat.py` `_reply`/`_fail` 429 branch (depends on P2's code
   string existing).
P4 frontend: types + service + store; test A4.
P5 env examples; full suite for A5.

### Risks
- RK1 (D1): `slowapi`'s default `_rate_limit_exceeded_handler` must never run —
  registering the app's own handler is what makes A1's `error_code` assertion pass;
  forgetting the registration silently ships slowapi's own JSON shape instead.
- RK2 (D2): `@limiter.limit(...)` locates the `Request` via the decorated function's
  signature; the handler must accept `request: Request` as a real parameter (not
  just available via `Depends`), or the decorator raises at call time.
- RK3 (D3/D4): `limits`' exact call surface (`MovingWindowRateLimiter.hit`/`.test`,
  `RateLimitItemPerMinute` construction) must be confirmed against the pinned
  version at execution time — this plan fixes the strategy (moving window) and the
  storage (in-memory), not the literal call signature.
- RK4 (D4): the rate-limit check must sit above `TurnTimeout`'s `asyncio.wait_for`
  wrapper — inside it, a rejection would race the budget clock and could report as
  a timeout instead (same class of bug the orchestrator already guards against for
  guardrails, PLAN precedent RK2 in the earlier rate-limit attempt).
- RK5 (D3): per-process, in-memory counters mean N replicas admit N x the configured
  limit; accepted for a single-replica dev deployment per R4, not fixed by this task.
- RK6 (D6): `rate_limit_default = ""` (gateway) and `rate_limit_*_rpm <= 0`
  (orchestrator) must both resolve to "admit everything" at construction time, not
  via a per-call branch, so a disabled limiter costs nothing on the hot path.
