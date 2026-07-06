# TASK — 2026-07-05-llm-request-timeout
owner: Engineer
immutable: true

## Requirements
- R1: Sub-agents hit the 120s budget with a bare "timed out": ChatOpenAI has no request
  timeout by default (OpenAI SDK waits up to 600s) and retries twice with backoff, so a
  slow/hanging NVIDIA call silently eats the whole budget. The factory must set an
  explicit per-request timeout and max_retries=1, configurable via env
  (LLM_REQUEST_TIMEOUT_S, default 90 — below the 120s sub-agent budget).

## Acceptance
- A1: build_chat_model(provider="nvidia"/"openai") passes timeout (from env override or
  90 default) and max_retries=1 to ChatOpenAI (stub runtime); file compiles.
