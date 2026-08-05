# VALIDATION — 2026-07-07-restructure-orchestrator-services

## v1

validation_version: 1
result: PASS
validated_against: PLAN v1, EXEC v1, working tree (mcp/master_orchestrator/**, backend rename)

### Requirements
- R1 PASS — `main.py` is a minimal entry point in web_agent shape: FastMCP construction,
  `start_job.register`/`delete_thread.register`, `main()` selecting transport (stdio ->
  `mcp.run`; http -> `HttpServer(...).run()`). No tool bodies / middleware / uvicorn /
  SDK-patch inline (re-checked full file).
- R2 PASS — `tools/` holds only `__init__.py`, `start_job.py`, `delete_thread.py`. Each is
  web_agent register() style, thin: single try -> service call -> `AgentResponse.ok`,
  except -> `AgentResponse.fail`. No loop/loader logic under `tools/`.
- R3 PASS — orchestration tool registered as `start_job`; gateway `orchestrator_tool`
  default == `start_job`; no bare `orchestrate` tool reference / string literal in
  mcp/master_orchestrator or backend (grep clean); `delete_thread` unchanged; gateway
  resolves the tool from the setting (agent_client.py:110), so runtime contract holds.
- R4 PASS — (a) `services/orchestrator.py` `class Orchestrator`; (b) `services/subagents.py`
  `class SubagentToolset`; (c) `services/http_server.py` `class HttpServer` +
  `_NormalizeHostMiddleware`. main.py/tools call into them.
- R5 PASS — behavior preserved by relocation: Orchestrator.run carries the identical turn
  logic (validate/thread-id/store/prompts/rehydrate/bounded loop/`asyncio.gather` fail-soft
  dispatch/`_inject_file`/exhausted-loop synthesis); helpers are now methods, call sites
  updated to `self.`/`SubagentToolset.load()`. HttpServer.run carries the identical serve
  path (shims, `http_app` allowed_hosts + TypeError fallback, uvicorn). Hand-compared
  against EXEC change list; no semantic drift.

### Acceptance
- A1 PASS — main.py forbidden-content grep (`@mcp.tool|uvicorn|Middleware|
  TransportSecurity|http_app`) finds none.
- A2 PASS — `ls tools/` == `__init__.py delete_thread.py start_job.py` (+__pycache__);
  no `orchestrator.py`/`subagents.py` under tools.
- A3 PASS — tool name `start_job`; no live `orchestrate` tool ref; `orchestrator_tool`
  default flipped.
- A4 PASS — `python3 -m compileall mcp/master_orchestrator` clean (re-run by Validator);
  AST sweep resolves every `from master_orchestrator.*` import (unresolved: NONE).
- A5 PASS — both tools return `AgentResponse[...]` with try/except fail-soft; gateway
  contract (`settings`-resolved tool name, `{"request": ...}` arg shape) unaffected — no
  gateway routing change in the diff.

### Issues
Blocking: none.

Non-blocking:
- {id: NB-1, type: logic, severity: medium, ref: EXEC test results,
  note: "Live mock e2e not runnable in sandbox (no PyPI/langchain/fastmcp, Py3.10). Change
  is behavior-neutral relocation + settings-default rename; validated via compile + layout
  + import-resolution + hand-comparison. Run `ORCHESTRATOR_LLM_PROVIDER` e2e once in a
  Py>=3.11 dev env before relying on it."}
- {id: NB-2, type: logic, severity: low, ref: mcp/master_orchestrator/memory.py,
  note: "Engineer follow-up requested moving memory.py into services/ too — out of THIS
  task's immutable scope (R4 named orchestration/subagent/http logic); tracked as a
  separate harness task."}
