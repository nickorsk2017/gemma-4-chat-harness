# EXEC — 2026-08-05-rate-limit-gateway-orchestrator
exec_version: 1

## v1

### Changed files
1. `backend/pyproject.toml` — added `slowapi>=0.1.9` dependency (P1).
2. `mcp/agent_core/pyproject.toml` — added `limits>=3.13.0` dependency (P2).
3. `backend/_common/env/settings.py` — `rate_limit_default: str = "30/minute"` (GATEWAY_ prefix, D6).
4. `backend/gateway/services/ratelimit.py` (NEW) — `slowapi.Limiter` keyed by `get_remote_address`; `default_limit_value()` reads settings live; `rate_limit_exceeded_handler` maps `RateLimitExceeded` -> `ApiResponse.fail` + `Retry-After` (deferred import of `chat._fail` to avoid an import cycle) (D1).
5. `backend/gateway/main.py` — registers `app.state.limiter`, the custom exception handler, `SlowAPIMiddleware` (before CORS) (D1).
6. `backend/gateway/routers/chat.py` — `Request` param + `@limiter.limit(default_limit_value)` on `/chat`, `/chat/files` (body param renamed `request`->`payload`); `_fail` gained optional `retry_after_s` (ceil, min 1); `_reply` gained `RATE_LIMITED_CODE` -> 429 branch beside `TURN_TIMEOUT_CODE` -> 504 (D2, D5).
7. `backend/gateway/services/agent_client.py` — `RATE_LIMITED_CODE = "rate_limited"`; `AgentOutcome.retry_after_s: float | None`; read from `meta.retry_after_s` in `_to_outcome` (D5).
8. `mcp/agent_core/ratelimit.py` (NEW) — `RateLimited(retry_after_s)` exception; `RateLimiter` wrapping `MovingWindowRateLimiter` + `MemoryStorage`, rpm read per-call, `<=0` disables with no storage touch (D3).
9. `mcp/agent_core/__init__.py` — exports `RateLimited`, `RateLimiter` (D3).
10. `mcp/master_orchestrator/config.py` — `rate_limit_thread_rpm: int = 20`, `rate_limit_global_rpm: int = 60` (ORCHESTRATOR_ prefix, D6).
11. `mcp/master_orchestrator/services/orchestrator.py` — `RATE_LIMITED_CODE`; module-level `_thread_limiter`/`_global_limiter`; `Orchestrator._check_rate_limits` runs at the top of `run`, before the `wait_for`/budget wrap; missing `thread_id` -> shared anonymous bucket (D3, D4).
12. `mcp/master_orchestrator/tools/start_job.py` — catches `RateLimited`, maps to `AgentResponse.fail(AGENT, str(exc), code=RATE_LIMITED_CODE, retry_after_s=exc.retry_after_s)`, mirrors the `TurnTimeout` catch (D4).
13. `frontend/types/chat.d.ts` — `ChatErrorCode` widened to `"turn_timeout" | "rate_limited"` (D7).
14. `frontend/services/chatService.ts` — `toErrorCode` narrows both codes (D7).
15. `frontend/stores/chatStore.ts` — `isTurnTimeout` generalized to `isRetryableFailure` (`RETRYABLE_CODES` set); existing placeholder/retryable/pending path reused unchanged (D7).
16. `backend/__tests__/test_rate_limit.py` (NEW) — A1 (429, `error_code == "rate_limited"`, positive integer `Retry-After`, agent client never called, second client unaffected), A2 (`/api/health` never limited). See deviation D-a below on path.
17. `mcp/__tests__/test_rate_limit.py` (NEW) — A3: per-thread bucket, global bucket, shared anonymous bucket, positive `retry_after_s`, disabled (`<=0`) buckets never reject, `start_job`-style envelope mapping; all assert `_run_turn` never reached on rejection. See deviation D-a.
18. `frontend/__tests__/chatStore.test.ts` — A4 case added: `rate_limited` reply produces the same retryable/pending state as `turn_timeout`.
19. `.env.example`, `backend/.env.example`, `mcp/.env.example` — documented `GATEWAY_RATE_LIMIT_DEFAULT`, `ORCHESTRATOR_RATE_LIMIT_THREAD_RPM`, `ORCHESTRATOR_RATE_LIMIT_GLOBAL_RPM`.

### Deviations from PLAN.md
- D-a (file paths, steps 16-17): PLAN.md names `backend/tests/test_rate_limit.py` and
  `mcp/tests/test_rate_limit.py`; the repo's actual current convention (every existing
  test file, e.g. `test_turn_timeout.py`) lives under `backend/__tests__/` and
  `mcp/__tests__/`. Placed new tests there instead, matching the real tree over the
  plan's stale path. No behavioral deviation.

### Test results
- `backend/__tests__/test_rate_limit.py`: 5/5 pass.
- `backend/__tests__` full suite: 5 new pass; 5 pre-existing failures in
  `test_chat_thread.py` / `test_uploads.py` (`FakeClient.send()` arity mismatch with
  `is_retry` arg) -- confirmed via `git stash` to fail identically with no plan changes
  applied; outside PLAN.md scope, not introduced by this change.
- `mcp/__tests__/test_rate_limit.py`: 6/6 pass. `test_turn_timeout.py`: 6/6 pass (no
  regression). Full `mcp/__tests__/`: 37 passed, 2 skipped.
- `mcp/guardrails/__tests__/*`: pre-existing collection errors
  (`ModuleNotFoundError: guardrails.tests`), leftover from an earlier rename, outside
  PLAN.md scope.
- Frontend jest: could not execute in this sandbox (arm64, no SWC binary/wasm,
  pnpm-managed node_modules, pnpm unavailable). Three frontend diffs reviewed by hand --
  small, mechanical, mirror the existing tested `turn_timeout` pattern exactly.
  **Open risk: A4 frontend test not actually run in this environment** -- recommend
  running `npm test`/`pnpm test` in the real dev environment before merge.
