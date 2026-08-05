# VALIDATION — 2026-07-07-agent-core-novita

## v1 — PASS
- A1 PASS: stub ChatOpenAI asserts Novita base_url + no extra_body; builds with
  GEMMA_API_KEY; caller-supplied provider/model/temperature correctly ignored
  (shared model, temp 0.5); cached; missing key -> LLMConfigError.
- A2 PASS: 5 build_chat_model call sites outside llm.py, signature unchanged;
  NVIDIA_* aliases preserved for config.py imports.
- Live Novita call left to Engineer (`make gemma-check` covers the same endpoint).
