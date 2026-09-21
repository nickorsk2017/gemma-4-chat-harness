# EXEC — 2026-09-21-fix-test-fakes-is-retry

## v1
- Step 1: backend/__tests__/test_chat_thread.py FakeClient.send now accepts `is_retry=False`.
- Step 2: backend/__tests__/test_uploads.py _CaptureClient.send now accepts `is_retry=False`.
