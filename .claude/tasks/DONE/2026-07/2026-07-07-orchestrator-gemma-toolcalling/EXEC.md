# EXEC — 2026-07-07-orchestrator-gemma-toolcalling

## v1
Rebuilt `mcp/master_orchestrator` from scratch (prior package deleted) per PLAN v1:
a Gemma tool-calling loop, no LangGraph/LangSmith, minimal surface.

Files (all new):
- `schemas/http.py` — `OrchestrateRequest` (prompt, context, thread_id),
  `SubTaskResult`, `OrchestrationResult`. Gateway contract unchanged (A1).
- `prompts/orchestrate.py` — single `ORCHESTRATOR_SYSTEM` routing prompt
  (prompts-as-data); tells the model to pass empty `text` for doc tools.
- `config.py` — env-backed sub-agent registry (`ORCHESTRATOR_*`), `doc_subagent`,
  `max_tool_iterations`, history/document caps. Sub-agent set is config-driven.
- `memory.py` — `InMemoryThreadStore` (history role/text dicts + documents by
  name), capped on save, thread isolation + `delete`. `db/` reserved for a
  durable backend (in-memory is the only store today).
- `tools/subagents.py` — dynamic tool discovery via `MultiServerMCPClient`
  (`get_tools(server_name=...)`); flags doc-sub-agent tools for text injection.
- `tools/orchestrator.py` — the loop: `get_llm().bind_tools(...)`, `ainvoke`,
  parallel `asyncio.gather` dispatch, fail-soft per call (R5), document text
  injected at dispatch (R6); persists history; iteration cap forces a final
  text answer if the model keeps requesting tools.
- `main.py` — FastMCP server: `orchestrate` -> AgentResponse[OrchestrationResult],
  `delete_thread` -> AgentResponse[dict], both fail-soft.
- `pyproject.toml` — `master-orchestrator` dist; drops langgraph /
  langgraph-checkpoint-postgres / langsmith (A2, A3).

Deviation from PLAN v1: Postgres store omitted — Engineer scoped this rebuild to a
minimal in-memory core; `memory.py`/`db/` leave the seam.

Verification:
- A5: all 12 modules byte-compile — pass.
- A2: grep finds no langgraph/langsmith/checkpointer/planner/graph — pass.
- Logic (deps-free): history cap, doc-text injection (default/named/empty),
  document text never rendered into the prompt, content flattening — pass.
- Full runtime (live LLM + spawned sub-agents) not exercisable here — left for Validator.

next_actor: Validator

## v2
Per PLAN v2 — swapped the thread store to a LangGraph checkpointer; loop untouched.
- `memory.py` — replaced `InMemoryThreadStore` with `CheckpointThreadStore` over a
  compiled no-op graph; `_build_checkpointer()` picks `AsyncPostgresSaver`
  (`ORCHESTRATOR_DATABASE_URL`, `.setup()` once, kept alive for the process) or
  `MemorySaver`. `get_store()` builds it lazily once inside the event loop. Store
  is now async. `ThreadState` is a dataclass (loop-facing view).
- `config.py` — added `database_url` (env `ORCHESTRATOR_DATABASE_URL`).
- `tools/orchestrator.py` / `main.py` — `await get_store()` + `await load/save/delete`.
- `pyproject.toml` — added `langgraph`, `langgraph-checkpoint-postgres`.
- `db/__init__.py` — note updated to the checkpointer-backed store.
Verify: all modules byte-compile; `langgraph` import confined to `memory.py` (grep);
loop dir (`tools/`) has no langgraph/StateGraph/checkpointer reference.
next_actor: Validator

## v3
Engineer-directed tightening: Postgres is the SINGLE source of thread data — the
MemorySaver fallback is removed. `memory.py` drops the MemorySaver import/branch;
`_build_checkpointer` raises `MemoryConfigError` when `ORCHESTRATOR_DATABASE_URL`
is unset and always builds `AsyncPostgresSaver`. Config comment updated to mark the
URL required. Byte-compiles; grep confirms no MemorySaver remains and langgraph
stays confined to memory.py.

## v3 — fix V1 (logic): restore HTTP serving path
- `config.py` — re-add `http_host` (0.0.0.0), `http_port` (8100), `http_allowed_hosts`
  (["mcp:8100","localhost:8100","127.0.0.1:8100"]); the Dockerfile's
  ORCHESTRATOR_HTTP_HOST/PORT env vars now bind again instead of being dropped by
  extra="ignore".
- `main.py` — restore `_run_http()` (uvicorn bind to http_host:http_port) plus the
  Host/DNS-rebinding shims (`_NormalizeHostMiddleware`,
  `_disable_sdk_rebinding_protection`, `_extend_fastmcp_guard_hosts`); `main()`
  branches to `_run_http()` for http/streamable-http, else `mcp.run(...)`. Restores
  PLAN v2 line 57 ("keep the fastmcp Host/rebinding shims"). `_export_langsmith_env`
  stays dropped per the same plan line.
- Effect: container serves the orchestrator on 0.0.0.0:8100/mcp; gateway
  (http://mcp:8100/mcp) connects again → chat 502 resolved.
- byte-compile: PASS. Tool contracts (orchestrate / delete_thread) unchanged (A1).
