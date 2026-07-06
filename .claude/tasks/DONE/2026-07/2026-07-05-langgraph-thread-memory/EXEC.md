# EXEC — 2026-07-05-langgraph-thread-memory
## v1

Implements PLAN v1 steps P1-P10.

### Changed files
- P1 mcp/master_orchestrator/pyproject.toml — + langgraph-checkpoint-postgres, psycopg[binary,pool]
- P2 mcp/master_orchestrator/config.py — + database_url (ORCHESTRATOR_DATABASE_URL),
  history_max_messages, document_max_chars
- P3 mcp/master_orchestrator/db/checkpointer.py — NEW: lazy process-wide saver
  (AsyncPostgresSaver over psycopg AsyncConnectionPool + setup(); InMemorySaver fallback),
  close_checkpointer() for tests/shutdown
- P4 mcp/master_orchestrator/tools/graph.py — persistent channels `messages`
  (add_messages) + `documents` (merge_documents reducer); HumanMessage appended on
  invoke, AIMessage in synthesize; deterministic extract_text injection for new
  pdf_path* (dedup vs planner tasks, injected results excluded from merged results);
  _harvest_documents stores {path: text}; compile-once graph bound to checkpointer;
  run_orchestration uses configurable.thread_id; format_history/format_documents caps
  from config
- P5 mcp/master_orchestrator/prompts/orchestrate.py — planner: history/documents
  placeholders + thread-memory rules (empty task list for memory-answerable
  follow-ups); synthesis: history + stored doc text, "never claim data missing"
- P6 mcp/master_orchestrator/schemas/http.py — OrchestrateRequest.thread_id (default "default")
- P7 backend/gateway/schemas/chat.py — ChatRequest.thread_id (opt), ChatReply.thread_id;
  backend/gateway/services/chat_service.py — uuid4 when absent, forward + echo;
  backend/gateway/services/orchestrator_client.py — thread_id through Protocol,
  _run_orchestration, both transports;
  backend/gateway/routers/chat.py — optional thread_id Form on /chat/files
- P8 frontend/types/chat.d.ts — threadId on request/response;
  frontend/services/chatService.ts — send thread_id (JSON + multipart), map reply;
  frontend/stores/chatStore.ts — threadId state: adopt from first reply, send on
  follow-ups, cleared by reset()
- P9 docker-compose.yml — postgres:17-alpine service (healthcheck, pgdata volume);
  mcp depends_on healthy postgres + ORCHESTRATOR_DATABASE_URL; .env.example POSTGRES_*
- P10 mcp/master_orchestrator/tests/test_memory.py — NEW: reducer, two-turn
  persistence over InMemorySaver, thread isolation, extract dedup;
  backend/tests/test_chat_thread.py — NEW: thread_id generate/forward/echo

### Notes
- Injected extract sub-tasks run in the same asyncio.gather as planned tasks (rule 6).
- No cross-agent imports: orchestrator reuses doc_analyzer.extract_text via MCP (K4).
- InMemorySaver fallback documented: cross-request memory in stdio gateway mode
  requires Postgres (D2 note).
