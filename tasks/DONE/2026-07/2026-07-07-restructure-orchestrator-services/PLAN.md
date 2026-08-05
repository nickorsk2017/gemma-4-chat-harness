# PLAN — 2026-07-07-restructure-orchestrator-services

## v1

### Target layout (mcp/master_orchestrator)
```
main.py                 # minimal entry point (web_agent shape) — R1
tools/
  __init__.py           # empty
  start_job.py          # register(mcp) -> @mcp.tool start_job          — R2 R3
  delete_thread.py      # register(mcp) -> @mcp.tool delete_thread      — R2
services/
  __init__.py           # empty (new)
  orchestrator.py       # class Orchestrator (was tools/orchestrator.py) — R4a
  subagents.py          # class SubagentToolset (was tools/subagents.py) — R4b
  http_server.py        # class HttpServer + _NormalizeHostMiddleware    — R4c
```
`tools/orchestrator.py` and `tools/subagents.py` are DELETED (moved). No other package
files change shape; `schemas/`, `prompts/`, `config.py`, `memory.py`, `db/` unchanged
except the schemas/http docstring (R3 naming).

### Architecture decisions
- D1 (R1, A1): `main.py` = build `FastMCP("master_orchestrator")`, call
  `start_job.register(mcp)` and `delete_thread.register(mcp)`, define `main()`.
  Transport selection stays in `main()` but delegates: stdio -> `mcp.run(transport=...)`;
  http/streamable-http -> `HttpServer(mcp, settings).run()`. No tool bodies, no middleware,
  no uvicorn, no SDK-patch functions inline (all relocated to `services/http_server.py`).
- D2 (R2, R3): `tools/start_job.py` mirrors `web_agent/tools/web_tools.py` — module-level
  `register(mcp)` closing over `@mcp.tool async def start_job(request: OrchestrateRequest)
  -> AgentResponse[OrchestrationResult]`, body = try `Orchestrator().run(request)` -> ok,
  except -> fail (fail-soft, A5). Tool name is `start_job` (the rename lives here). `AGENT`
  constant defined per tool module (web_agent convention).
- D3 (R2): `tools/delete_thread.py` — module-level `register(mcp)` closing over
  `@mcp.tool async def delete_thread(thread_id) -> AgentResponse[dict]`, body unchanged in
  effect (get_store -> delete -> ok/fail envelope).
- D4 (R4a, R5): `services/orchestrator.py` exposes `class Orchestrator` with `async
  run(request) -> OrchestrationResult` carrying the exact current turn logic from
  `tools/orchestrator.py` (validate, thread-id gen, store load/save, PromptGenerator
  system prompts, rehydrate history, bounded tool-calling loop, `asyncio.gather` fail-soft
  dispatch, file injection, exhausted-loop synthesis fallback). The current module helpers
  (`_validate`, `_dispatch`, `_inject_file`, `_rehydrate`, `_text`) become methods
  (static where they hold no state). No behavior change — pure relocation into a class.
- D5 (R4b): `services/subagents.py` exposes `class SubagentToolset` holding `tools`,
  `by_name`, `file_tool_names` (was the `LoadedTools` dataclass) with an async classmethod
  `load()` performing the current `MultiServerMCPClient` discovery from `settings.subagents`
  / `settings.file_subagents`. `Orchestrator` calls `SubagentToolset.load()` and reads its
  fields (replaces the free function `load_subagent_tools` and dataclass `LoadedTools`).
- D6 (R4c, R5): `services/http_server.py` exposes `class HttpServer(mcp, settings)` with
  `run()` = the current `_run_http` body (apply shims, build `mcp.http_app` with
  `allowed_hosts`/middleware + TypeError fallback, uvicorn serve). The ASGI
  `_NormalizeHostMiddleware` class and the two shims (`_disable_sdk_rebinding_protection`,
  `_extend_fastmcp_guard_hosts`) move here as the middleware class + private methods.
  Behavior identical; only the home changes.
- D7 (R3 propagation): rename `orchestrate` -> `start_job` in the gateway tool-name
  setting default (`backend/_common/env/settings.py` `orchestrator_tool`) and fix naming
  in docstrings/comments that call the tool `orchestrate` (schemas/http.py header,
  backend/gateway/services/agent_client.py header). `delete_thread` unchanged. The
  gateway resolves the tool by the `orchestrator_tool` setting (env-overridable), so the
  runtime contract holds once the default flips (A3, A5).

### File impact map
| File | Action | Req |
|---|---|---|
| mcp/master_orchestrator/main.py | rewrite (minimal entry point; delegate http to service) | R1 A1 |
| mcp/master_orchestrator/tools/start_job.py | new (register-style thin tool; name=start_job) | R2 R3 |
| mcp/master_orchestrator/tools/delete_thread.py | new (register-style thin tool) | R2 |
| mcp/master_orchestrator/tools/orchestrator.py | delete (logic -> services/orchestrator.py) | R4a |
| mcp/master_orchestrator/tools/subagents.py | delete (logic -> services/subagents.py) | R4b |
| mcp/master_orchestrator/services/__init__.py | new (empty) | R4 |
| mcp/master_orchestrator/services/orchestrator.py | new (class Orchestrator) | R4a R5 |
| mcp/master_orchestrator/services/subagents.py | new (class SubagentToolset) | R4b R5 |
| mcp/master_orchestrator/services/http_server.py | new (class HttpServer + middleware) | R4c R5 |
| mcp/master_orchestrator/schemas/http.py | modify (docstring tool name) | R3 |
| backend/_common/env/settings.py | modify (orchestrator_tool default -> start_job) | R3 |
| backend/gateway/services/agent_client.py | modify (docstring tool name) | R3 |

### Steps
- P1 (R4b): create `services/__init__.py` + `services/subagents.py` (`SubagentToolset`,
  async classmethod `load()`) — no dependents yet.
- P2 (R4a R5): create `services/orchestrator.py` (`Orchestrator.run` + helper methods),
  consuming `SubagentToolset.load()`; logic copied verbatim from `tools/orchestrator.py`.
- P3 (R4c R5): create `services/http_server.py` (`HttpServer.run`, `_NormalizeHostMiddleware`,
  two shim methods) from the current `main.py` http machinery.
- P4 (R2 R3): create `tools/start_job.py` and `tools/delete_thread.py` (register-style,
  thin, fail-soft), calling the service classes.
- P5 (R1 A1): rewrite `main.py` to the minimal shape (FastMCP + register calls + `main()`
  delegating http to `HttpServer`).
- P6 (R4a R4b): delete `tools/orchestrator.py` and `tools/subagents.py`.
- P7 (R3): flip `backend/_common/env/settings.py orchestrator_tool` default to
  `start_job`; update tool-name wording in `schemas/http.py` and
  `backend/gateway/services/agent_client.py` docstrings.
- P8 (A1-A5): run verification (below); record in EXEC.md.

### Risks / notes
- Import direction is one-way (main -> tools -> services -> config/memory/prompts/schemas);
  no cycle introduced. Executor must confirm no residual importer of
  `master_orchestrator.tools.orchestrator` / `.subagents` / `load_subagent_tools` /
  `LoadedTools` remains (only `main.py` imported the tools module today — repo grep).
- Rename completeness: besides the setting default, check for any deploy-time override
  pinning the tool name (docker-compose / `.env` `ORCHESTRATOR_TOOL` or gateway
  `*_ORCHESTRATOR_TOOL`). If one pins `orchestrate`, update it; if none, note it. Do NOT
  change gateway routing logic — only the resolved tool name.
- Behavior-preservation is the bar (R5): the loop/dispatch/file-injection/synthesis code
  and the http shim code are relocated as-is; Validator checks for semantic drift, not
  just that files moved.

### Verification (Executor runs; Validator re-checks)
- `python3 -m compileall mcp/master_orchestrator` clean (A4).
- `ls mcp/master_orchestrator/tools` == `__init__.py start_job.py delete_thread.py`
  (+`__pycache__`); no `orchestrator.py`/`subagents.py` under tools (A2).
- AST/import sweep: every `from master_orchestrator.*` resolves; `main.py` has no
  `@mcp.tool`, no `uvicorn`, no `Middleware`, no `TransportSecurity` reference (A1).
- grep: no live tool named `orchestrate` in `mcp/master_orchestrator` + `backend`
  (docstrings updated); `orchestrator_tool` default == `start_job` (A3).
- Static fail-soft check: both tools keep try/except -> `AgentResponse.fail` (A5).
- Env-blocked (document, per prior tasks): full dep install + live mock e2e — sandbox has
  no PyPI/`langchain`/`fastmcp`; relocation is behavior-neutral so static + compile
  evidence is the gate. Flag as non-blocking if unrun.
