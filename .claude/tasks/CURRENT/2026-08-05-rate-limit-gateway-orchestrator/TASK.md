# TASK — 2026-08-05-rate-limit-gateway-orchestrator
owner: Engineer
immutable: true

## Requirements
- R1: The gateway MUST rate-limit inbound chat traffic per client, implemented with
  the `slowapi` library (Starlette/FastAPI middleware built on top of the `limits`
  package). Scope, limited endpoints, and key-extraction strategy are Planner
  decisions, but `/api/health` MUST stay unlimited.
- R2: The orchestrator MUST enforce its own independent limit on the same turn path
  (defence in depth), using a `Limiter` from the `limits` package (the library
  `slowapi` itself wraps), so a caller reaching the agent directly, bypassing the
  gateway, is still bounded.
- R3: An over-limit request MUST be rejected before any billable or stateful work
  (no LLM call, no guardrails call, no sub-agent dispatch, no thread write) and MUST
  surface as HTTP 429 with a `Retry-After` header, in the existing `ApiResponse.fail`
  envelope, at the gateway -- including when the rejection originates in the
  orchestrator.
- R4: Limits MUST be configurable via the existing per-service settings objects
  (env-driven) with safe defaults for a single-replica dev deployment.
- R5: The frontend MUST surface a 429 as a retryable failure using the existing retry
  affordance, not a silent generic error.

## Acceptance
- A1: A gateway test drives a client over the configured limit and asserts 429,
  `error_code == "rate_limited"`, a positive integer `Retry-After`, and that the
  agent client was never called; a second client is unaffected.
- A2: A gateway test asserts `/api/health` is never limited.
- A3: An orchestrator test asserts an over-limit turn is rejected via the `limits`
  `Limiter` with no LLM call, no guardrails call, and no store write, and that the
  gateway maps that outcome to 429 + `Retry-After`.
- A4: A frontend test asserts a 429 reply produces the retry-able state, not a bare
  error message.
- A5: Existing gateway, orchestrator, and frontend tests still pass.

## Constraints
- Runtime dependencies: `slowapi` MAY be added to `backend/pyproject.toml`; `limits`
  MAY be added to `backend/pyproject.toml` and `mcp/*/pyproject.toml`. No other new
  runtime dependency (no Redis/Postgres-backed limiting; in-memory storage only).
- English only in all files (root CLAUDE.md).
- Supersedes the hand-rolled token-bucket design from the earlier, abandoned
  `2026-08-05-rate-limit` task (see `.claude/tasks/DONE/2026-08/2026-08-05-rate-limit/`)
  -- that task never reached EXECUTED and no rate-limit code exists in the current
  tree; this task starts fresh with `slowapi` / `limits` as the mandated libraries.
