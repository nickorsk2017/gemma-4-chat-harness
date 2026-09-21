# PLAN — 2026-09-21-fix-test-fakes-is-retry

## v1
- Root cause: commit c95d3bf added positional `is_retry` to `AgentClient.send` and to the `ChatService` call site; fakes in two tests were not updated (test_rate_limit.py fake already was).
- Step 1: backend/__tests__/test_chat_thread.py `FakeClient.send` signature -> `(self, prompt, file=None, thread_id=None, is_retry=False)`.
- Step 2: backend/__tests__/test_uploads.py `_CaptureClient.send` signature -> same.
- Verify: run backend pytest (A1).
