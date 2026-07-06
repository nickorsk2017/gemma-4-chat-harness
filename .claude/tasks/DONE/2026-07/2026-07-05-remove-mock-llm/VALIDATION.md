# VALIDATION — 2026-07-05-remove-mock-llm

## v1 — PASS
Sandbox without PyPI: py_compile + source asserts + stub-module runtime tests; no network.

- A1 PASS: build_chat_model raises LLMConfigError for provider="mock", api_key=None and
  api_key=""; with a key returns ChatOpenAI(model=google/gemma-4-31b-it,
  base_url=https://integrate.api.nvidia.com/v1).
- A2 PASS: zero occurrences of FakeListChatModel / mock_responses / _MOCK_PLAN /
  _llm_ready / `llm_provider == "mock"` in mcp/**/*.py.
- A3 PASS (stub runtime): summarize_document -> DocSummary prompt contains extracted doc
  text + max_points; ask_document -> DocAnswer prompt contains question + doc text;
  factory called with nvidia/gemma/NVIDIA base_url; no NotImplementedError on LLM paths.
- A4 PASS: 9 files compile; `git grep nvapi-` empty.

Residual risk (non-blocking): live structured-output behavior of gemma on the NVIDIA
endpoint unverified here; first keyed run should smoke-test one orchestrate round-trip.
Note: agents now REQUIRE GEMMA_API_KEY at first LLM use (fail-fast by design).
