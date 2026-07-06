# PLAN — 2026-07-05-langgraph-thread-memory
## v1

### Decisions
- D1 (R1,R4): Memory lives in master_orchestrator — the owner of the LangGraph graph.
  Gateway stays stateless; frontend only carries `thread_id`.
- D2 (R1,R5): Checkpointer = `AsyncPostgresSaver` (langgraph-checkpoint-postgres) on a
  psycopg async pool. Created lazily as a module singleton; `.setup()` on first use.
  Graph compiled ONCE with the checkpointer (replace per-request build_graph()).
  No `ORCHESTRATOR_DATABASE_URL` -> `InMemorySaver` fallback (dev/local).
  Note: gateway stdio mode spawns the orchestrator per request, so only the Postgres
  saver gives cross-turn memory there; in-memory fallback persists only within a
  long-lived orchestrator process (http/docker mode).
- D3 (R1,R2): OrchestratorState gains persistent channels:
  `messages` (add_messages reducer) and `documents` (dict path->extracted text,
  dict-merge reducer). Per-turn channels (request/tasks/results/answer) overwrite.
- D4 (R2): Deterministic PDF capture — not LLM-dependent: dispatch node appends one
  `doc_analyzer.extract_text` sub-task (parallel, per rule 6) for every `pdf_path*`
  in context not already in `state.documents`; a post-dispatch merge stores the
  extracted text into `documents`. LLM-planned tasks still run unchanged.
- D5 (R3): Prompt enrichment (prompts stay data, rule 4):
  planner prompt += recent history (capped, last N=10 messages) + known stored docs,
  and a rule that memory-only follow-ups may return ZERO sub-tasks;
  synthesis prompt += history + stored document text (capped chars/doc) so follow-ups
  are answered from the thread even with no sub-task results.
- D6 (R4,R6): Contracts (contracts first, rule 2):
  OrchestrateRequest.thread_id: str (gateway always sends);
  ChatRequest.thread_id: str|None (optional, back-compat), ChatReply.thread_id echoed;
  /api/chat/files gains optional `thread_id` form field;
  frontend: SendMessageRequest/Response +threadId; chatStore holds threadId
  (adopt from first reply, reset on clearChat).
- D7 (R5): docker-compose: `postgres` service (pinned major, healthcheck, named
  volume); `mcp` depends_on healthy postgres; env ORCHESTRATOR_DATABASE_URL; also
  document in .env.example if present.

### Steps
- P1: mcp/master_orchestrator/pyproject.toml — add langgraph-checkpoint-postgres,
  psycopg[binary,pool].
- P2: master_orchestrator/config.py — add `database_url: str|None` (env-backed).
- P3: master_orchestrator/db/checkpointer.py — saver singleton: build async Postgres
  saver from settings or InMemorySaver; run setup() once; async-safe init.
- P4: master_orchestrator/tools/graph.py — state channels+reducers (D3), deterministic
  extract task injection + documents merge (D4), compile-once with checkpointer,
  run_orchestration(request) uses configurable.thread_id, append HumanMessage(prompt)
  on entry and AIMessage(answer) at synthesize.
- P5: master_orchestrator/prompts/orchestrate.py — extend PLANNER_* and SYNTHESIS_*
  per D5 (history + documents placeholders).
- P6: master_orchestrator/schemas/http.py — thread_id on OrchestrateRequest.
- P7: backend gateway — schemas/chat.py (thread_id in/out), services/chat_service.py
  (uuid4 when missing, forward, echo), services/orchestrator_client.py (pass through),
  routers/chat.py (optional thread_id Form on /chat/files).
- P8: frontend — types/chat, services/chatService.ts (send/receive threadId),
  stores/chatStore.ts (hold/adopt/reset threadId).
- P9: docker-compose.yml — postgres service + volume + healthcheck + env wiring (D7).
- P10: tests — mcp: state reducers/doc-capture/thread persistence over InMemorySaver;
  backend: thread_id generation+echo; run existing backend/mcp/frontend suites.

### Risks
- K1: async saver needs a running loop at init -> lazy init inside first orchestrate
  call, not at import.
- K2: unbounded growth of history/doc text in prompts -> caps in D5 (N messages,
  chars/doc) from config, not constants.
- K3: checkpoint size: full doc text stored per thread — acceptable for 15MB PDF cap
  (text is far smaller); out-of-scope RAG noted in TASK.
- K4: pypdf already extracts in doc_analyzer; orchestrator reuses its extract_text
  tool (no cross-agent import, rule: agents share only via MCP).
