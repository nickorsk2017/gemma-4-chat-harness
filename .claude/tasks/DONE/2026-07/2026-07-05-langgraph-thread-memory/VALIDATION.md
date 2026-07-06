# VALIDATION — 2026-07-05-langgraph-thread-memory
## v1 — PASS

### Checks
- R1: graph compiled once with checkpointer; AsyncPostgresSaver via psycopg pool +
  setup(); add_messages channel; thread_id -> configurable.thread_id. CONFORMS (EXEC P3/P4).
- R2: deterministic extract_text injection per new pdf_path* + _harvest_documents ->
  persistent `documents` channel; dedup vs planner-created extract tasks. CONFORMS.
- R3: planner + synthesis prompts receive history/stored-doc text; empty-task-list rule
  for memory-answerable follow-ups; synthesis instructed never to claim missing data
  when stored text present. CONFORMS.
- R4: thread_id end-to-end (Zustand store -> chatService JSON/multipart -> ChatRequest/
  Form -> OrchestratorClient -> OrchestrateRequest). Gateway generates uuid4 hex when
  absent and echoes it; store adopts it on first reply, clears on reset. CONFORMS.
- R5: compose adds postgres:17-alpine (healthcheck, pgdata volume); mcp gets
  ORCHESTRATOR_DATABASE_URL + depends_on healthy; InMemorySaver fallback when unset.
  CONFORMS. YAML parses.
- R6: all new wire fields optional/defaulted (ChatRequest.thread_id opt, ChatReply.
  thread_id defaulted, OrchestrateRequest.thread_id default "default"; /chat/files
  form field optional). Envelope untouched. CONFORMS.
- Static: py_compile PASS on all changed .py; needle conformance PASS; compose YAML PASS.

### Environment limitation (non-blocking, disclosed)
Sandbox blocks PyPI (allowlist) and node_modules are darwin-native — pytest/jest
could NOT be executed here. New suites are in-repo and must be run by the Engineer:
- `cd backend && pytest tests/test_chat_thread.py`
- `cd mcp && pip install -e agent_core -e master_orchestrator && pytest master_orchestrator/tests/test_memory.py`
- `cd frontend && pnpm test`
- e2e: `make up`, upload a PDF, ask a follow-up without re-attaching.
Classified as verification debt, not a defect in the change; acceptance A4 (run
suites) rests with the Engineer's environment.

### Issues
(none blocking)

result: PASS
