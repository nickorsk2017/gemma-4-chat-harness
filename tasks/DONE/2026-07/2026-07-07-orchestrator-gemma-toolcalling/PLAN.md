# PLAN — 2026-07-07-orchestrator-gemma-toolcalling

## v1

### Design decision
Replace the LangGraph `plan -> dispatch -> synthesize` graph and its structured-output
Planner with a single **Gemma tool-calling agent loop**. The model owns routing: it is
bound the sub-agents' tool schemas and emits `tool_calls`; the orchestrator executes them
(fail-soft, in parallel) and returns `ToolMessage`s until the model emits a final text
answer. This removes the Planner as a separate reasoning stage — routing is now the
model's native tool selection — and removes LangGraph entirely.

Rationale: the Planner + graph existed only to (a) pick sub-tasks and (b) merge results.
A tool-calling model does both natively and handles follow-ups (call nothing, answer from
memory) without a special "empty plan" path. Fewer moving parts, no graph/checkpointer.

### Tool discovery & binding
- `subagent_client.get_bound_tool_schemas()` fetches each configured sub-agent's tools via
  the existing `MultiServerMCPClient`, converts them to OpenAI tool dicts, and returns
  `(schemas, name->agent map)`. For doc_analyzer tools the injected `text` field is stripped
  from the schema so the model neither sees nor supplies document text (R6).
- Discovery is dynamic (config-driven), so it stays correct as sub-agents change (the old
  hardcoded planner prompt had already drifted: web_agent now exposes only `search_web`).

### Orchestration loop (`tools/orchestrator.py`, replaces graph.py + planner.py)
1. Load thread memory (history + stored docs) for `request.thread_id`.
2. Deterministically capture any new gateway document (`document_text`/`document_name`) into
   the store — no LLM, no sub-agent (preserves the "no extract round-trip" behavior).
3. Build messages: system prompt + prior history + human(prompt + non-document context hints
   + stored-document name list).
4. Loop (bounded by `max_tool_iterations`): `model_with_tools.ainvoke(messages)`.
   - If the AI message has `tool_calls`: run them concurrently with `asyncio.gather` via
     `call_subagent` (fail-soft envelopes). For doc_analyzer calls inject stored text first.
     Record a `SubTaskResult` per call (against the model's args, minus injected text).
     Append the AI message + one `ToolMessage` per call, then continue the loop.
   - Else: the content is the final answer -> break.
5. Persist the new human turn + final AI answer to the store; return
   `OrchestrationResult(prompt, answer, results)`.

### Thread memory (`memory.py`, replaces db/checkpointer.py)
- `ThreadStore` protocol with `load(thread_id) -> ThreadState(messages, documents)`,
  `save(thread_id, messages, documents)`, `delete(thread_id)`.
- `InMemoryThreadStore` (default) and `PostgresThreadStore` (when
  `ORCHESTRATOR_DATABASE_URL` set) storing one JSON row per thread. Built lazily, once,
  inside the event loop (async), mirroring the old checkpointer lifecycle.
- Messages persisted as plain role/text dicts (no LangChain message pickling); rehydrated to
  `HumanMessage`/`AIMessage` for the prompt. History capped by `history_max_messages`,
  document text capped by `document_max_chars` when rendered into prompts.

### Schema / prompt / config / deps deltas
- schemas/plan.py: drop `Plan` (planner-only); keep `AgentName`, `SubTask`, `SubTaskResult`,
  `OrchestrationResult`.
- prompts/orchestrate.py: drop PLANNER_* and SYNTHESIS_*; add one `ORCHESTRATOR_SYSTEM`
  prompt describing routing rules, file/context handling, and memory behavior.
- config.py: drop LangSmith settings; keep sub-agent registry, timeouts, `database_url`,
  history/document caps; add `max_tool_iterations`.
- main.py: drop `_export_langsmith_env`; keep the fastmcp Host/rebinding shims.
- pyproject.toml: remove langgraph, langgraph-checkpoint-postgres, langsmith. Keep psycopg
  (own Postgres store), langchain-core, langchain-mcp-adapters, langchain-openai (via
  agent_core), pydantic(-settings), fastmcp, agent-core.
- Docs: update mcp/README.md, mcp/CLAUDE.md, master_orchestrator description to the
  tool-calling design (no langgraph/langsmith claims).

### Risks / mitigations
- Model loops forever -> bound by `max_tool_iterations`; on exhaustion, do a final no-tools
  call to force an answer.
- Tool-name collision across servers -> current tool names are unique; map validates and the
  loop fails soft on unknown tool.
- Postgres store scope creep -> keep it a single JSON blob per thread; behavior identical to
  in-memory, only durability differs.

### Test strategy
Rewrite tests/test_memory.py against the new loop + store using a fake tool-calling model
(scripts a tool_call then a final answer) and a fake `call_subagent`: assert doc capture w/o
sub-agent, cross-turn history+doc persistence, thread isolation, doc-text injection (and
non-leak into results), and delete_thread. Byte-compile the whole package.

## v2
Engineer-directed change (reverses R2 for thread memory only): thread state MUST be
persisted via a **LangGraph checkpointer** keyed by `thread_id` — Postgres
(`AsyncPostgresSaver`) when `ORCHESTRATOR_DATABASE_URL` is set, else `MemorySaver`.

Scope: memory layer ONLY. The Gemma tool-calling loop (`tools/orchestrator.py`),
routing, parallel fail-soft dispatch and doc-text injection are unchanged; LangGraph
does not re-enter the orchestration path. A trivial no-op single-node graph is
compiled solely to expose the checkpointer's thread-keyed state through
`aget_state`/`aupdate_state`. Store API becomes async (`await load/save/delete`).
