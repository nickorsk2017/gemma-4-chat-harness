# TASK — 2026-07-05-llm-timeout-budgets
owner: Engineer
immutable: true

## Requirements
- R1: LangSmith trace (project gemma-chat) shows summarize_document killed at the 120s
  sub-agent cap: first gemma HTTP attempt hangs to the 90s LLM timeout, the retry
  (~30s typical) no longer fits. Make one hung attempt + one retry fit inside the
  sub-agent budget: lower the per-request LLM timeout to 45s stack-wide.
- R2: Give the gateway headroom over the pipeline (plan + dispatch + synthesize):
  raise GATEWAY_ORCHESTRATOR_TIMEOUT_S 180 -> 240 in .env.
- R3: Env-only fix — no code changes. LLM_REQUEST_TIMEOUT_S is already read by
  agent_core.llm._request_timeout(); compose must forward it to the mcp service.

## Acceptance
- A1: compose mcp env has LLM_REQUEST_TIMEOUT_S (default 45); backend keeps
  GATEWAY_ORCHESTRATOR_TIMEOUT_S passthrough (value via .env).
- A2: .env sets LLM_REQUEST_TIMEOUT_S=45, GATEWAY_ORCHESTRATOR_TIMEOUT_S=240;
  examples document both.
- A3: Budget math holds: 2*45 < 120 (subagent) and 90+120+2*45(+slack) < 240*... 
  plan(<=90) + dispatch(<=120) + synthesize(<=90) = 300 worst case documented; typical
  path fits 240 and a hung call now degrades gracefully instead of killing the turn.

## Constraints
- docker-compose.yml, .env, .env.example, mcp/.env.example only.
