# TASK — 2026-07-05-llm-timeouts
owner: Engineer
immutable: true

## Requirements
- R1: "orchestrator timed out" at ~30s: real chain = planner LLM + sub-agent (pypdf +
  gemma over full doc) + synthesis LLM. Budgets must nest: per-sub-agent < gateway total.
- R2: defaults: ORCHESTRATOR_SUBAGENT_TIMEOUT_S 30 -> 120; GATEWAY orchestrator_timeout_s
  30 -> 180. Compose passes both explicitly; mcp/.env.example updated.

## Acceptance
- A1: settings defaults changed (source check); compose sets GATEWAY_ORCHESTRATOR_TIMEOUT_S
  and ORCHESTRATOR_SUBAGENT_TIMEOUT_S; example env matches; py_compile clean.
