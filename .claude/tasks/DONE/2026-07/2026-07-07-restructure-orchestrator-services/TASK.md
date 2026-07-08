# TASK — 2026-07-07-restructure-orchestrator-services
owner: Engineer
immutable: true

## Requirements
- R1: Slim `mcp/master_orchestrator/main.py` to a minimal entry point in the shape of
  `mcp/web_agent/main.py`: construct `FastMCP("master_orchestrator")`, register the tools
  via per-tool `register(mcp)` calls, and expose `main()`. No business logic, no HTTP
  serving machinery, and no SDK/host-guard shims left inline in `main.py`.
- R2: `mcp/master_orchestrator/tools/` must contain ONLY MCP-tool modules — one file per
  tool, `web_agent`-style (module-level `register(mcp)` with a nested `@mcp.tool`):
  `start_job.py` and `delete_thread.py`. Each tool stays thin: validate -> call a service
  -> wrap in the `agent_core` `AgentResponse` envelope (fail-soft, never raise across the
  MCP boundary). No orchestration/loop/loader logic remains under `tools/`.
- R3: Rename the orchestration MCP tool `orchestrate` -> `start_job` everywhere it is
  named, including the gateway's `orchestrator_tool` setting default, so the gateway calls
  the renamed tool. `delete_thread` keeps its name.
- R4: All remaining (non-tool) logic moves into `mcp/master_orchestrator/services/` as
  classes: (a) the orchestration loop currently in `tools/orchestrator.py`; (b) the
  sub-agent tool loader currently in `tools/subagents.py`; (c) the HTTP-serving + host /
  DNS-rebinding-shim machinery currently inline in `main.py`. `main.py` and the tools call
  into these service classes.
- R5: Behavior is preserved. The orchestration turn logic (validation, thread-id
  generation, memory load/save, tool-calling loop, parallel fail-soft dispatch, file
  injection, synthesis fallback) and the HTTP transport behavior (Host normalization,
  rebinding-protection disable, fastmcp guard-host extension, uvicorn serve) are unchanged
  in effect — only relocated and reshaped into classes.

## Acceptance
- A1: `mcp/master_orchestrator/main.py` contains no `@mcp.tool` bodies, no middleware
  class, no uvicorn/serve code, and no SDK-patch functions — only FastMCP construction,
  `register` calls, and `main()`/transport selection delegating to a service.
- A2: `ls mcp/master_orchestrator/tools/` lists exactly `__init__.py`, `start_job.py`,
  `delete_thread.py` (plus `__pycache__`). No `orchestrator.py` / `subagents.py` remain
  under `tools/`.
- A3: The registered orchestration tool is named `start_job`; `grep -rn "orchestrate"`
  across `mcp/master_orchestrator` and `backend` finds no live reference to a tool named
  `orchestrate` (docstrings/comments updated); the gateway `orchestrator_tool` default is
  `start_job`.
- A4: `mcp/master_orchestrator/services/` holds the orchestration, subagent-loader, and
  HTTP-server classes; every `from master_orchestrator.*` import in the package resolves;
  `python3 -m compileall mcp/master_orchestrator` is clean.
- A5: The `start_job` and `delete_thread` tools return `AgentResponse[...]` and never
  raise across the MCP boundary (fail-soft try/except retained); the gateway agent_client
  contract (tool-name from settings, `{"request": ...}` arg shape) still holds.

## Constraints
- Scope: `mcp/master_orchestrator/**`, and the minimal backend touch to rename the tool
  (`backend/_common/env/settings.py` default, plus any docstring/comment naming the tool).
  No change to sub-agent logic, gateway routing behavior, memory store, schemas' data
  shape, or the `OrchestrateRequest`/`OrchestrationResult` contracts.
- `web_agent` register() style for tools (module-level `register(mcp)`), per Engineer.
- Follow subsystem rules in `mcp/CLAUDE.md`: prompts stay in `prompts/`, settings in
  `config.py`, single typed envelope across boundaries.
