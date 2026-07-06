# VALIDATION — 2026-07-05-web-agent-gemma-llm

## v1 — PASS
Sandbox has no PyPI; validated via py_compile + source asserts + stub-module runtime test
of providers (both branches). No network calls.

- A1 PASS: with key set, providers build the model via agent_core.build_chat_model with
  exactly {provider: nvidia, model: google/gemma-4-31b-it, base_url: NVIDIA endpoint,
  api_key} and route through with_structured_output(NewsResult|Weather|WebPage).
- A2 PASS: without key, all three providers return prior mock objects; 7 files compile.
- A3 PASS: `git check-ignore .env` -> ignored; `git grep nvapi-` over tracked files empty;
  GEMMA_API_KEY alias present in all 4 configs, zero stale NVIDIA_API_KEY refs.
- R4/R5 PASS: prompts in web_agent/prompts/generate.py; web_tools.py untouched.

Residual risk (non-blocking): with_structured_output end-to-end against the live NVIDIA
endpoint not exercised here — verify with one real call in a keyed environment.
