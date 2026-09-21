# TASK — 2026-09-21-fix-test-fakes-is-retry
owner: Engineer
immutable: true

## Requirements
- R1: CI backend pytest fails: ChatService calls client.send(prompt, file, thread_id, is_retry) but test fakes FakeClient (test_chat_thread.py) and _CaptureClient (test_uploads.py) do not accept is_retry. Make backend tests pass.

## Acceptance
- A1: `pytest backend/__tests__` passes with 0 failures.

## Constraints
- Test-only change; production code (chat_service.py, agent_client.py) unchanged.
