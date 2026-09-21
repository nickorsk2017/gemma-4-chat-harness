# PLAN — 2026-09-21-fix-guardrails-test-imports

## v1
- Root cause: `guardrails/tests` renamed to `guardrails/__tests__`; imports not updated.
- Step 1: in test_lexicon.py, test_pii.py, test_pipeline.py, test_injection_corpus.py replace `guardrails.tests.fixtures` with `guardrails.__tests__.fixtures`.
- Step 2: update stale docstring reference in mcp/__tests__/test_guardrail_gates.py to `guardrails/__tests__`.
- Verify: run mcp, backend pytest and frontend jest exactly as harness-gate.yml does.

## v2
- Finding after v1: with collection fixed, 99 async tests in guardrails/__tests__ fail under `pytest mcp` because the CI configfile is mcp/pyproject.toml (asyncio STRICT); `asyncio_mode = "auto"` in guardrails/pyproject.toml only applies when run from mcp/guardrails.
- Step 3: add `@pytest.mark.asyncio` to every `async def test` in guardrails/__tests__ (test_pipeline.py, test_injection_corpus.py), matching the convention in mcp/__tests__.
- Finding: frontend jest (next CI step, never reached) fails 2 tests in __tests__/chatStore.test.ts: the reload simulation calls `setState`, which the persist middleware writes to localStorage, erasing the slice before `rehydrate()`.
- Step 4: add a `simulateReload()` helper in chatStore.test.ts that captures the stored slice, wipes in-memory state, and restores storage; use it in both rehydrate tests.
