# PLAN — 2026-07-05-reset-chat-delete-thread

## v1

### Strategy
Deletion flows down the existing call chain — frontend service -> gateway REST ->
orchestrator MCP tool -> LangGraph checkpointer — adding one narrow "delete thread"
capability at each layer. No layer gains new knowledge of another's internals.

### Impact map (sequenced)
1. `mcp/master_orchestrator/tools/orchestrate_tools.py` — second MCP tool
   `delete_thread(thread_id)`: obtain the process checkpointer, call its async
   thread-deletion API (`adelete_thread`, available in the pinned langgraph line for
   both InMemorySaver and AsyncPostgresSaver), return the standard AgentResponse
   envelope (ok -> {thread_id, deleted:true}; error -> fail envelope).
2. `backend/_common/env/settings.py` — `orchestrator_delete_tool: str = "delete_thread"`
   (config, not constants — mirrors `orchestrator_tool`).
3. `backend/gateway/services/orchestrator_client.py` — extend the Protocol with
   `delete_thread(thread_id) -> OrchestrationOutcome`; shared `_run_tool` helper
   (generalizes `_run_orchestration`) used by both stdio and http clients; parse the
   AgentResponse envelope fail-soft (ok flag only; no answer expected).
4. `backend/gateway/schemas/chat.py` — `DeleteThreadReply {thread_id, deleted:bool}`.
5. `backend/gateway/services/chat_service.py` — `delete_thread(thread_id)`: validate
   non-empty id (else GatewayValidationError), call client, map failure -> GatewayError.
6. `backend/gateway/routers/chat.py` — `DELETE /api/chat/threads/{thread_id}` ->
   envelope via the existing try/except pattern (400/502/500).
7. `frontend/services/chatService.ts` — `deleteChatThread(threadId)`: DELETE to the
   gateway, parse envelope, throw ChatServiceError on failure.
8. `frontend/stores/chatStore.ts` — `clearThread(): Promise<boolean>`: no threadId ->
   `reset()`, true; else call service; success -> `reset()`, true; failure -> set
   `error`, false. Store never touches `window` — reload is the view's job.
9. `frontend/shared/ui-kit/HeaderButton.tsx` (new primitive, RULE-B) — small labeled
   action button for header bars; presentational only.
10. `frontend/shared/features/chat/ChatView.tsx` — header becomes a flex row; right
    side renders the HeaderButton ("Reset chat"); handler awaits `clearThread()` and
    on true calls `window.location.reload()`; disabled while a send/reset is running.
11. Tests: `backend/tests/test_chat_thread.py` (+delete cases with FakeClient: happy,
    orchestrator-fail, empty id), `frontend/__tests__/chatStore.test.ts` (+clearThread
    cases incl. localStorage wipe), keep all existing suites green.

### Risks
- Checkpointer deletion API availability -> pinned `langgraph>=1.0` /
  `langgraph-checkpoint-postgres>=2.0` expose `adelete_thread`; Executor asserts the
  attribute and returns a fail envelope if absent (fail-soft, no 500).
- stdio mode spawns a fresh orchestrator per call: InMemorySaver deletion is a no-op
  across processes — acceptable; real persistence (Postgres) is the target.
- Reload-vs-error UX -> reload happens ONLY on success (R5) so errors stay visible.

### Sequencing
mcp tool (1) -> gateway chain (2-6) -> frontend chain (7-10) -> tests (11) ->
frontend `tsc` + behavior harness; backend/mcp: static review + host-run note
(sandbox has no Python deps/PyPI).
