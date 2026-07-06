# TASK — 2026-07-05-reset-chat-delete-thread
owner: Engineer
immutable: true

## Requirements
- R1: Chat header gets a "reset chat" button on the RIGHT side.
- R2: Clicking it calls the backend, which deletes the conversation's stored
  messages by `thread_id` (orchestrator thread memory: messages + documents)
  and returns a success envelope.
- R3: On success the frontend clears its persisted local state (localStorage
  slice from task 2026-07-05-persist-thread-localstorage) and RELOADS the chat
  page.
- R4: Empty chat (no `thread_id` yet): the button clears local state and
  reloads without calling the backend.
- R5: Backend failure: show the store error, do NOT clear local state, do NOT
  reload (the thread stays usable).

## Acceptance
- A1: `DELETE {API}/api/chat/threads/{thread_id}` -> `{status:"Success", data:{deleted:...}}`;
  gateway relays the deletion to the orchestrator (MCP tool), which removes the
  thread from the LangGraph checkpointer (Postgres or in-memory).
- A2: UI: button visible at the right of the header; click -> request -> page reload -> empty chat.
- A3: A new message after reset starts a NEW `thread_id` (no old context in replies).
- A4: Tests: gateway service/router delete path (fake client); frontend store
  clear-thread action; existing suites stay green. `tsc --noEmit` clean.

## Constraints
- Follow existing layer rules: gateway stays an MCP client (never imports mcp/
  packages); frontend store delegates HTTP to `services/`; header button is a
  ui-kit primitive (RULE-B); components < 200 LOC (RULE-A).
- Envelope + honest status codes (400/502/500) as in existing chat routes.
- No new runtime dependencies.
