# TASK — 2026-08-05-rate-limit
owner: Engineer
immutable: true

## Requirements
- R1: The gateway MUST rate-limit inbound chat traffic per client IP. The limited
  surface is every request-consuming endpoint under `/api/chat` (JSON chat, multipart
  chat/files, thread deletion). `/api/health` MUST stay unlimited.
- R2: The client IP MUST be derived from the connection peer, with a proxy-forwarded
  header honoured only when the deployment declares itself to be behind a trusted
  proxy (config flag, default off). An untrusted `X-Forwarded-For` MUST NOT be able
  to change the bucket a caller falls into.
- R3: The orchestrator MUST enforce its own independent limit on the same turn path,
  so a caller reaching the agent directly (bypassing the gateway) is still bounded.
  The orchestrator's limit is defence in depth, not a duplicate of R1's counter.
- R4: An over-limit request MUST be rejected, not queued. The gateway MUST answer
  HTTP 429 in the standard `ApiResponse.fail` envelope with `error_code`
  `rate_limited` and a `Retry-After` header carrying whole seconds until the caller
  may retry. An orchestrator-side rejection MUST surface as the same 429 +
  `Retry-After` at the gateway, not as a generic 502.
- R5: Rejection MUST happen before any billable or stateful work: no LLM call, no
  guardrails call, no sub-agent dispatch, no thread write.
- R6: Counters live in process memory. The rate limiter implementation MUST use the
  `limits` Python library (added as a runtime dependency to `backend/pyproject.toml`
  and `mcp/*/pyproject.toml`) with its in-memory storage backend; NO new service, NO
  new container, NO Redis/Postgres backend. The per-process/per-replica nature of the
  limit MUST be stated in the code that implements it.
- R7: Limits MUST be configurable through the existing settings objects (env-driven,
  per service) and MUST ship with defaults that are safe for a single-replica dev
  deployment. Setting a limit to 0 or below MUST disable that limiter.
- R8: Memory used by the limiter MUST be bounded: idle keys are reclaimed, so a burst
  of distinct IPs cannot grow the process footprint without limit.
- R9: The frontend MUST surface a 429 as an actionable failure the user can re-send,
  reusing the existing retry affordance rather than introducing a second one, and
  MUST NOT silently swallow it into the generic error string.
- R10: The rate-limited turn MUST NOT be recorded in thread history on either side.

## Acceptance
- A1: A gateway test drives the same client over the configured limit and asserts
  429, `error_code == "rate_limited"`, a positive integer `Retry-After`, and that the
  agent client was never called.
- A2: A gateway test asserts requests under the limit are unaffected and that two
  different client IPs do not share a bucket.
- A3: A gateway test asserts `/api/health` is never limited.
- A4: An orchestrator test asserts an over-limit turn returns the typed rate-limit
  outcome with no LLM call, no guardrails call and no store write, and that the
  gateway maps that outcome to 429 + `Retry-After`.
- A5: A test asserts a limiter configured with a non-positive limit admits everything.
- A6: A test asserts idle keys are reclaimed (R8) rather than accumulating.
- A7: A frontend test asserts a 429 reply produces the retry-able state, not a bare
  error message.
- A8: Existing gateway, orchestrator and frontend tests still pass; the guardrails
  and turn-timeout contracts are unchanged.

## Constraints
- The `limits` Python library MAY be added as a runtime dependency to
  `backend/pyproject.toml` and `mcp/*/pyproject.toml` for rate limiting; no other new
  runtime dependency is permitted there or in `frontend/package.json`. A hand-rolled
  token-bucket implementation is out of scope now that `limits` covers it.
- The gateway stays a pure proxy in spirit: the limiter is an edge/transport concern
  and MUST NOT introduce business logic or validation into the gateway.
- English only in all files (root CLAUDE.md). User-visible frontend copy follows the
  existing UI language convention already present in the store.
- Redis/Postgres-backed limiting is explicitly out of scope for this task; the design
  MUST leave room for it without requiring it.
