# TASK — 2026-07-05-gemma-nvidia-llm
owner: Engineer
immutable: true

## Requirements
- R1: All MCP agents' LLM access must go through `google/gemma-4-31b-it` served by the
  NVIDIA OpenAI-compatible endpoint `https://integrate.api.nvidia.com/v1` (via
  `langchain_openai.ChatOpenAI` with `base_url`).
- R2: Add a `nvidia` provider to the shared factory `mcp/agent_core/llm.py`
  (`build_chat_model`), supporting a configurable `base_url`.
- R3: Every agent config with LLM settings (`master_orchestrator`, `doc_analyzer`) defaults to
  provider `nvidia`, model `google/gemma-4-31b-it`, NVIDIA base URL. Agents without LLM
  settings that may need one (`web_agent`, `image_analyzer`) gain the same LLM settings block.
- R4: API key is NEVER hardcoded. All agents read the single env var `NVIDIA_API_KEY`
  (validation_alias in each config).
- R5: Preserve zero-key dev experience: with no `NVIDIA_API_KEY` set, agents fall back to the
  mock model exactly as today.

## Acceptance
- A1: `build_chat_model(provider="nvidia", ...)` returns `ChatOpenAI` pointed at the NVIDIA
  base URL with the gemma model.
- A2: With `NVIDIA_API_KEY` unset, all agent configs import cleanly and LLM paths resolve to mock.
- A3: With `NVIDIA_API_KEY` set, orchestrator planner/graph build the gemma model (unit-level
  check, no live network call required).
- A4: Existing imports pass; no other behavior changes.

## Constraints
- No real network calls in validation.
- Scope limited to factory + configs; doc_analyzer real chains stay NotImplementedError.
- Follow mcp/CLAUDE.md conventions (pydantic-settings, type hints, async-first untouched).
