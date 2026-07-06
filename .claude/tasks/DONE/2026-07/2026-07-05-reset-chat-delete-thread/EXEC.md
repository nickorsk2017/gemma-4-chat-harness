# EXEC — 2026-07-05-reset-chat-delete-thread

## v1 (implements PLAN v1, all 11 steps)

### Changes
- mcp: `master_orchestrator/tools/orchestrate_tools.py` — new `delete_thread(thread_id)`
  MCP tool: validates id, `(await get_checkpointer()).adelete_thread(key)`, AgentResponse
  ok/fail envelope (fail-soft).
- backend:
  - `_common/env/settings.py` — `orchestrator_delete_tool="delete_thread"`,
    `orchestrator_delete_timeout_s=30.0`.
  - `gateway/services/orchestrator_client.py` — Protocol + both clients gain
    `delete_thread`; call body refactored into shared `_call_tool` (used by
    `_run_orchestration` and new `_run_delete`); `_parse_ack` for ack envelopes.
  - `gateway/schemas/chat.py` — `DeleteThreadReply{thread_id, deleted}`.
  - `gateway/services/chat_service.py` — `delete_thread`: blank id -> GatewayValidationError;
    client failure -> GatewayError.
  - `gateway/routers/chat.py` — `DELETE /api/chat/threads/{thread_id}` with the standard
    400/502/500 envelope pattern.
- frontend:
  - `services/chatService.ts` — `deleteChatThread(threadId)` (DELETE, envelope parse,
    ChatServiceError on failure).
  - `stores/chatStore.ts` — `clearThread()`: no thread -> local reset only (R4); success ->
    reset (persist middleware wipes localStorage slice); failure -> error set, state kept,
    returns false (R5).
  - `shared/ui-kit/HeaderButton.tsx` — new presentational primitive (RULE-B), 30 LOC.
  - `shared/features/chat/ChatView.tsx` — header is a flex row; right side "Reset chat"
    HeaderButton; `handleReset` reloads the page only when `clearThread()` returns true;
    disabled while sending/before hydration. 118 LOC (RULE-A ok).
- tests: `backend/tests/test_chat_thread.py` +3 delete cases (happy/blank-id/orchestrator-fail);
  `frontend/__tests__/chatStore.test.ts` +3 clearThread cases incl. persisted-slice wipe.

### Verification runs (sandbox)
- `npx tsc --noEmit` -> clean.
- `python3 -m py_compile` on all touched Python files -> OK.
- Frontend behavior harness (compiled store + service stub + localStorage stub):
  delete-by-thread_id, local+persisted wipe, empty-after-reload, new thread after reset,
  no-backend-call-without-thread, failure keeps transcript+error -> ALL PASSED.
- pytest / jest / next lint cannot run in this sandbox (no Python deps, PyPI and npm
  registries unreachable, macOS-built node_modules) -> host-run required (A4 residual);
  same limitation as the previous task, recorded for the Validator.
