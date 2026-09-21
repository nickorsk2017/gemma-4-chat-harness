# EXEC — 2026-09-21-fix-guardrails-test-imports

## v1
- Step 1: `guardrails.tests.fixtures` -> `guardrails.__tests__.fixtures` in test_lexicon.py, test_pii.py, test_pipeline.py, test_injection_corpus.py.
- Step 2: docstring in mcp/__tests__/test_guardrail_gates.py now references `guardrails/__tests__`.
- Step 3: `@pytest.mark.asyncio` added to 28 async tests in test_pipeline.py and 2 in test_injection_corpus.py.
- Step 4: `simulateReload()` helper added to frontend/__tests__/chatStore.test.ts and used in both rehydrate tests.
