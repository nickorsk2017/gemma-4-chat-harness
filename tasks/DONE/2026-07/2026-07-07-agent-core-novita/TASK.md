# TASK — 2026-07-07-agent-core-novita
owner: Engineer
immutable: true

## Requirements
- R1: Provider changed to Novita for the whole app. Rewrite `mcp/agent_core/llm.py`:
  base_url `https://api.novita.ai/openai`, key from `GEMMA_API_KEY` (Novita key in
  root .env / container env), default model `google/gemma-4-31b-it`
  (override via GEMMA_MODEL).
- R2: Drop the OpenRouter-specific `extra_body={"reasoning": ...}` — not part of
  Novita's OpenAI-compatible surface.
- R3: Public API unchanged: build_chat_model signature, get_llm, LLMConfigError,
  NVIDIA_* aliases, timeout/max_retries behavior, app-wide temperature 0.5.

## Acceptance
- A1: Model builds against Novita with GEMMA_API_KEY; missing key -> LLMConfigError.
- A2: Consumers (providers.py x3, planner.py, graph.py) need no changes.
