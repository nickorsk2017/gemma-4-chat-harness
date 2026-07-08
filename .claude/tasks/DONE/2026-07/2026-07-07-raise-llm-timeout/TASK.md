# TASK — 2026-07-07-raise-llm-timeout
owner: Engineer
immutable: true

## Requirements
- R1: Raise the per-attempt LLM HTTP timeout `LLM_REQUEST_TIMEOUT_S` from 45 to
  90 so document (and other) LLM calls over large context stop hitting "Request
  timed out". 90 matches the code default in agent_core.llm.DEFAULT_REQUEST_TIMEOUT_S.
- R2: Keep the documented invariant "2 x LLM_REQUEST_TIMEOUT_S must fit within
  ORCHESTRATOR_SUBAGENT_TIMEOUT_S" truthful: raise ORCHESTRATOR_SUBAGENT_TIMEOUT_S
  120 -> 200 (2x90=180 < 200). Note: the sub-agent budget is documentation-only
  (not enforced in code today), so the effective change is the LLM timeout.
- R3: Apply the new values everywhere the timeout is defined: the user's runtime
  root `.env` (currently overrides to 45), the docker-compose defaults, and
  mcp/.env.example. Update the accompanying comment.

## Acceptance
- A1: root .env, docker-compose.yml defaults, and mcp/.env.example all show
  LLM_REQUEST_TIMEOUT_S=90 and ORCHESTRATOR_SUBAGENT_TIMEOUT_S=200.
- A2: 2 x 90 (=180) < 200 invariant holds; no code logic changed; no secrets
  altered in root .env (only the timeout line).

## Constraints
- Config only: root .env (timeout line), docker-compose.yml, mcp/.env.example.
  No Python changes.
