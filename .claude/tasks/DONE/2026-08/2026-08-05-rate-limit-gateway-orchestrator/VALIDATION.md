# VALIDATION — 2026-08-05-rate-limit-gateway-orchestrator
validation_version: 1

## v1

result: PASS

### Requirement/acceptance conformance
- R1/A2: `/api/health` has no `@limiter.limit` decorator (chat.py); confirmed by a
  passing test hammering it after exhausting the `/chat` bucket. Delete-thread
  endpoint also excluded, matching D2.
- R3/A1/D1: 429 uses real `ApiResponse.fail` envelope via deferred `chat._fail` call
  from `ratelimit.py`'s exception handler; `Retry-After` = `max(1, ceil(retry_after_s))`,
  always a positive integer; custom handler registered before `SlowAPIMiddleware`
  (RK1 avoided).
- R2/D3/D4/RK4: `Orchestrator.run` calls `self._check_rate_limits(...)` as the literal
  first statement, before `self._deadline` / `asyncio.wait_for(_run_turn(...))`; a
  rejection raises before any LLM/guardrails/store call. Verified by test execution,
  not just static read.
- start_job.py: `RateLimited` caught before the `TurnTimeout` catch, mapped to
  `AgentResponse.fail(AGENT, str(exc), code=RATE_LIMITED_CODE, retry_after_s=...)`,
  mirrors existing pattern.
- agent_client.py: `RATE_LIMITED_CODE` mirrored; `AgentOutcome.retry_after_s` added;
  `_to_outcome` reads `meta.get("retry_after_s")`.
- chat.py `_reply`: `RATE_LIMITED_CODE` -> 429 + `Retry-After` branch beside the
  existing `TURN_TIMEOUT_CODE` -> 504 branch.
- R5/A4: `ChatErrorCode` widened; `toErrorCode` narrows both codes;
  `isRetryableFailure`/`RETRYABLE_CODES` cover both; `chatStore.test.ts` A4 case is
  logically sound (asserts `retryable: true`, `error === null`, `pending` populated)
  though not executed in-sandbox (no SWC binary for arm64 jest).
- R4/D6: dependencies limited to `slowapi` + `limits`, both in-memory
  (`MemoryStorage`), no Redis/Postgres.
- English-only: confirmed across all changed/new files.

### Test execution (independently re-run, not trusted from EXEC.md alone)
- `backend/__tests__/test_rate_limit.py`: 3/3 pass.
- Full `backend/__tests__/`: 5 pass, 5 pre-existing unrelated failures
  (`FakeClient.send()` arity mismatch in `test_chat_thread.py`/`test_uploads.py`,
  confirmed pre-existing via `git stash`) -- matches EXEC.md.
- `mcp/__tests__/test_rate_limit.py`: 6/6 pass. Full `mcp/__tests__/`: 37 passed,
  2 skipped -- matches EXEC.md.
- `mcp/guardrails/__tests__/*`: 4 pre-existing collection errors, unrelated
  (leftover from an earlier rename) -- matches EXEC.md.
- Frontend jest: not executable in this sandbox (arm64, no SWC binary, pnpm
  unavailable); reviewed by hand, logically correct. **A5 residual risk**: run
  `npm test`/`pnpm test` for `frontend/__tests__/chatStore.test.ts` in the real dev
  environment before/at next opportunity to close this gap with an actual run.

### Issues
None blocking. No requirement, architecture, or logic issues found.
