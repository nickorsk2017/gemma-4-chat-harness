# PLAN — 2026-08-05-rate-limit
plan_version: 1

## v1

### D1 — Algorithm: token bucket (satisfies R1,R3,R4)
One bucket per key: capacity = burst, refilled continuously at rate = limit/60s.
Chosen over a fixed window because the window's boundary admits 2x the limit in one
instant, and over a sliding log because the log's memory grows with traffic (R8).
The bucket also yields an honest `Retry-After` for free: the time until one token
accrues, which a window can only approximate. Admission is a pure arithmetic update
of (tokens, last_refill) — no I/O, no await — so it is atomic under a single event
loop and needs no lock; concurrency notes belong in the module docstring, not a mutex.

### D2 — Two implementations, one contract (R6, backend rule 7)
`backend/` may not import `mcp/` and vice versa, so the limiter exists twice, exactly
as `FilePayload` and `TURN_TIMEOUT_CODE` already do. Both copies expose the same tiny
surface (construct with rpm+burst; `check(key) -> allowed | retry_after_s`) and each
docstring names the other as its mirror. The gateway copy lives in `backend/_common/`
(shared service infrastructure, alongside `env/` and `schemas/`); the agent copy lives
in `mcp/agent_core/` so guardrails and any future agent inherit it without a second
rewrite. No third-party dependency: a token bucket is ~40 lines and every candidate
library (slowapi, limits) drags in either a Redis client or a starlette version pin.

### D3 — Gateway enforcement point: ASGI middleware (R1,R5)
Registered in `create_app()` after CORS, before the router. Middleware, not a route
dependency, because it must reject before FastAPI parses the body — a 15 MiB
multipart upload is exactly the request we least want to have already read (R5), and
a `Depends` runs after parsing. Path scope is a prefix match on the settings-declared
limited prefix (`/api/chat`), so `/api/health` and anything added later outside the
prefix are unlimited by construction (R1) rather than by an exemption list that will
rot. CORS stays outermost so a 429 still carries CORS headers — otherwise the browser
reports it as a network error and the UI cannot act on it (R9).

### D4 — Client identity (R2)
`request.client.host` is the default and the only trusted source. A new setting
`rate_limit_trust_proxy` (default false) switches on reading the left-most entry of
`X-Forwarded-For`; with it off the header is ignored entirely, so a caller cannot
choose its own bucket by sending one. Default-off is the safe default: a
direct-exposed deployment that honoured the header would have no limit at all.
When no peer is knowable the request is bucketed under a single fallback key —
unattributable traffic shares one bucket rather than escaping the limiter.

### D5 — Orchestrator enforcement point and key (R3,R5)
The agent has no HTTP request object, so the gateway's key is not reachable and must
not be faked: adding a client-supplied `client_id` to `OrchestrateRequest` would give
a direct caller — the exact caller R3 is about — a free choice of bucket. The
orchestrator therefore keys on what it can verify itself, with two buckets checked in
`Orchestrator.run` before anything else in the turn:
1. per-`thread_id` (absent thread_id -> one shared anonymous bucket): stops a single
   conversation, human or scripted, from monopolising the fleet;
2. process-global: the ceiling that actually bounds LLM spend when a direct caller
   rotates thread_ids.
The check runs before `_files.validate`, before `check_input`, before `store.load`
and therefore before any LLM, guardrails or checkpointer call (R5, R10). No thread
state is loaded, so nothing can be written (R10). `OrchestrateRequest` is unchanged,
so no gateway contract change follows from this.

### D6 — Rejection path, end to end (R4)
Code string `rate_limited`, mirrored on both sides like `turn_timeout`:
- orchestrator: typed `RateLimited(retry_after_s)` raised by the limiter check in
  `services/orchestrator.py`; caught in `tools/start_job.py` and returned as
  `AgentResponse.fail(..., code="rate_limited", retry_after_s=...)` — the envelope's
  `**meta` already carries arbitrary keys, so no schema change (contrast `turn_timeout`,
  which needs nothing but a code).
- gateway client: `AgentOutcome` gains `retry_after_s: float | None`, read from the
  envelope's meta next to the existing `meta.code` read.
- gateway middleware: rejects on its own limiter without ever calling the agent.
- router `_reply`: maps `error_code == "rate_limited"` to 429, mirroring the existing
  504/`turn_timeout` branch; both the middleware's and the agent's 429 go out through
  one helper that sets `Retry-After` (whole seconds, ceiling, minimum 1 — 0 would tell
  a client to retry immediately, which is the opposite of the intent) on the standard
  `ApiResponse.fail` envelope.

### D7 — Bounded memory (R8)
Buckets are reclaimed lazily inside `check`, amortised: every N-th call sweeps entries
whose bucket has been full for longer than the refill-to-full interval — a full bucket
is indistinguishable from an absent one, so dropping it changes no decision. No
background task, no timer, nothing to stop on shutdown. The sweep interval is an
implementation constant, not config: it affects only memory, never behaviour.

### D8 — Configuration (R7)
Gateway (`_common/env/settings.py`, `GATEWAY_` prefix): `rate_limit_rpm` (default 30),
`rate_limit_burst` (default 10), `rate_limit_trust_proxy` (default false),
`rate_limit_path_prefix` (default `/api/chat`).
Orchestrator (`master_orchestrator/config.py`, `ORCHESTRATOR_` prefix):
`rate_limit_thread_rpm` (default 20), `rate_limit_global_rpm` (default 120),
`rate_limit_burst` (default 5). Defaults are sized for a single-replica dev stack and
sit above normal human use — a turn costs up to 66s, so 30/min per IP is already far
past what one browser can generate. rpm <= 0 disables that limiter by returning a
no-op admitter at construction, not by a branch on every call (R7).

### D9 — Frontend (R9)
`ChatErrorCode` becomes `"turn_timeout" | "rate_limited"`; `toErrorCode` narrows both.
In the store, `isTurnTimeout` generalises to a retryable-code predicate — the existing
placeholder + `retryable: true` + `pending` path is reused unchanged, so a 429 gets the
same button the timeout already has and no second affordance appears. The two cases
differ only in placeholder text; the rate-limit copy follows the store's existing
UI-language convention and says to wait before retrying.

### File-by-file
1. `backend/_common/ratelimit.py` (NEW) — token bucket + limiter registry, no deps.
2. `backend/_common/__init__.py` — export the limiter.
3. `backend/_common/env/settings.py` — the four `rate_limit_*` settings of D8.
4. `backend/gateway/middleware/__init__.py`, `backend/gateway/middleware/ratelimit.py`
   (NEW) — ASGI middleware: path-prefix scope, key extraction (D4), 429 envelope +
   `Retry-After`.
5. `backend/gateway/main.py` — register the middleware inside `create_app()` (after CORS).
6. `backend/gateway/services/agent_client.py` — `RATE_LIMITED_CODE`; `AgentOutcome.retry_after_s`;
   read `meta.retry_after_s` in `_to_outcome`.
7. `backend/gateway/routers/chat.py` — `_fail` gains an optional `Retry-After`; `_reply`
   maps `rate_limited` -> 429.
8. `mcp/agent_core/ratelimit.py` (NEW) — the mirrored limiter (D2) + `RateLimited`
   exception carrying `retry_after_s`.
9. `mcp/agent_core/__init__.py` — export both.
10. `mcp/master_orchestrator/config.py` — the three `rate_limit_*` settings of D8.
11. `mcp/master_orchestrator/services/orchestrator.py` — module-level limiters built from
    settings; the two checks at the top of `run` (D5).
12. `mcp/master_orchestrator/tools/start_job.py` — catch `RateLimited` -> `AgentResponse.fail`
    with code + `retry_after_s` (D6).
13. `frontend/types/chat.d.ts` — widen `ChatErrorCode`.
14. `frontend/services/chatService.ts` — narrow both codes in `toErrorCode`.
15. `frontend/stores/chatStore.ts` — retryable-code predicate + rate-limit placeholder (D9).
16. `backend/tests/test_rate_limit.py` (NEW) — A1,A2,A3,A5,A6.
17. `mcp/tests/test_rate_limit.py` (NEW) — A4 agent side (no LLM/guardrails/store call).
18. `frontend/__tests__/chatStore.test.ts` — A7 case appended.
19. `.env.example`, `backend/.env.example`, `mcp/.env.example` — document the new knobs.
20. `README.md` — one line in configuration: the limit is per process, per replica (R6).

### Sequencing
P1 `_common/ratelimit.py` + tests A5,A6 (the shared primitive, provable alone).
P2 gateway settings + middleware + registration; tests A1,A2,A3.
P3 `agent_core/ratelimit.py` mirror + orchestrator settings.
P4 orchestrator checks in `run` + `start_job` mapping; test A4 (agent side).
P5 gateway `AgentOutcome.retry_after_s` + router 429 mapping; test A4 (gateway side).
P6 frontend types/service/store + test A7.
P7 env examples + README line; full suite for A8.

### Risks
- RK1 (D3): a middleware that reads the body would defeat R5. It must decide on scope
  and headers only, and pass the receive channel through untouched.
- RK2 (D5): the orchestrator's check must sit above the `try` that converts timeouts —
  a rate-limit rejection reported as `turn_timeout` would make the UI promise a retry
  that is guaranteed to fail again immediately.
- RK3 (D6): the code string exists in four places (agent, gateway client, router,
  frontend). Same drift risk as `turn_timeout`; mitigated the same way — a named
  constant per side and a comment pointing at the mirror.
- RK4 (D1/D7): a monotonic clock is required. Wall-clock time going backwards (NTP)
  would hand out free tokens or an absurd `Retry-After`.
- RK5 (R6/D8): per-process counters mean N replicas admit N x the limit. Accepted and
  documented (item 20); the `check(key)` surface is what a Redis backend would later
  implement without touching call sites.
