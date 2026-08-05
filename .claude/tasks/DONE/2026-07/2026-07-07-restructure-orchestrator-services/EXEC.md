# EXEC — 2026-07-07-restructure-orchestrator-services

## v1

### Per-step summary
- P1 (R4b): `services/__init__.py` (empty) + `services/subagents.py` — `SubagentToolset`
  dataclass (fields `tools`/`by_name`/`file_tool_names`) with async classmethod `load()`;
  discovery body copied verbatim from the old `tools/subagents.py` (`MultiServerMCPClient`
  over `settings.subagents`, file-tool flagging via `settings.file_subagents`).
- P2 (R4a R5): `services/orchestrator.py` — `class Orchestrator` with `async run(request)`;
  the full turn logic moved from `tools/orchestrator.py` unchanged (validate, thread-id gen,
  store load/save, PromptGenerator prompts, rehydrate, bounded loop, `asyncio.gather`
  fail-soft dispatch, file injection, exhausted-loop synthesis fallback). Former module
  helpers are now instance methods (`_validate/_dispatch/_inject_file/_rehydrate/_text`);
  `run()` calls `SubagentToolset.load()` (replaces `load_subagent_tools`).
- P3 (R4c R5): `services/http_server.py` — `class HttpServer(mcp, settings)` with `run()`
  (former `_run_http` body), the `_NormalizeHostMiddleware` ASGI class, and the two shims
  as `_disable_sdk_rebinding_protection` (staticmethod) / `_extend_fastmcp_guard_hosts`
  (uses `self._settings.http_allowed_hosts`). Serve behavior identical.
- P4 (R2 R3): `tools/start_job.py` and `tools/delete_thread.py` — web_agent register()
  style (module-level `register(mcp)` + nested `@mcp.tool`), thin (service call wrapped in
  try/except -> `AgentResponse.ok/fail`). Orchestration tool registered as `start_job`.
- P5 (R1 A1): `main.py` rewritten to minimal shape — `FastMCP` + `start_job.register` +
  `delete_thread.register` + `main()` (stdio -> `mcp.run`; http/streamable-http ->
  `HttpServer(mcp, settings).run()`, imported lazily inside the branch).
- P6 (R4a R4b): deleted `tools/orchestrator.py` and `tools/subagents.py` (+ their .pyc).
- P7 (R3): `backend/_common/env/settings.py` `orchestrator_tool` default -> `start_job`;
  tool-name wording fixed in `schemas/http.py` header and
  `backend/gateway/services/agent_client.py` header. No override pins the name
  (docker-compose/.env grep: none), so the setting default is the only runtime change.

### Changed files
- mcp/master_orchestrator/main.py (rewritten, minimal)
- mcp/master_orchestrator/tools/start_job.py (new)
- mcp/master_orchestrator/tools/delete_thread.py (new)
- mcp/master_orchestrator/tools/orchestrator.py (deleted)
- mcp/master_orchestrator/tools/subagents.py (deleted)
- mcp/master_orchestrator/services/__init__.py (new, empty)
- mcp/master_orchestrator/services/orchestrator.py (new)
- mcp/master_orchestrator/services/subagents.py (new)
- mcp/master_orchestrator/services/http_server.py (new)
- mcp/master_orchestrator/schemas/http.py (docstring tool name)
- backend/_common/env/settings.py (orchestrator_tool default -> start_job)
- backend/gateway/services/agent_client.py (docstring tool name)

### Deviations from PLAN
- None. Layout, class shapes, and step order match PLAN v1.

### Test results
- RAN/PASSED — `python3 -m compileall -q mcp/master_orchestrator` clean (exit 0);
  `py_compile` on the two edited backend files clean (sandbox Python 3.10, syntax-level).
- RAN/PASSED — A1 sweep: `main.py` has no `@mcp.tool`, `uvicorn`, `Middleware`,
  `TransportSecurity`, or `http_app` (grep: none).
- RAN/PASSED — A2 layout: `tools/` == `__init__.py delete_thread.py start_job.py`
  (+`__pycache__`); no `orchestrator.py`/`subagents.py` under `tools/`.
- RAN/PASSED — A3 rename: no bare `orchestrate` tool reference in mcp/master_orchestrator
  or backend; no `"orchestrate"`/`'orchestrate'` literal repo-wide; `orchestrator_tool`
  default == `start_job`.
- RAN/PASSED — A4 imports: AST sweep resolves every `from master_orchestrator.*` import to
  an existing module (unresolved: NONE); no residual importer of
  `tools.orchestrator`/`tools.subagents`/`load_subagent_tools`/`LoadedTools`/
  `run_orchestration`.
- SKIPPED (env-blocked, per PLAN) — full dep install + live mock e2e: sandbox has no
  PyPI / `langchain` / `fastmcp` (prior tasks record the same limit). The change is a
  behavior-neutral relocation (logic bytes moved into classes; the rename is a settings
  default + docstrings), so compile + layout + import-resolution evidence is the gate.
  Validator to re-run mock e2e in a Py>=3.11 dev env before relying on it (NB).
