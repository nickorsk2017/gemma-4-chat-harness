# VALIDATION — 2026-07-07-orchestrator-gemma-toolcalling

## v1 — exec_version=2 — FAIL

### Checks
- A5 byte-compile: PASS — every module in `master_orchestrator` compiles.
- A2/A3 dead-code removal: PASS — no `tools.planner`/`tools.graph`/`db.checkpointer`
  imports remain; `langgraph` survives only in `memory.py`, sanctioned by PLAN v2
  (thread memory backed by a LangGraph checkpointer).
- A1 gateway contract / reachability: FAIL (blocking) — see V1.

### V1 (blocking) — HTTP serving path removed; gateway cannot reach the orchestrator
- type: logic
- severity: critical
- ref: master_orchestrator/main.py, master_orchestrator/config.py
- PLAN v2 line 57 requires: "main.py: drop `_export_langsmith_env`; keep the
  fastmcp Host/rebinding shims." The executed `main.py` dropped them entirely and
  now calls only `mcp.run(transport=settings.transport)` with no host/port.
- Effect: the Dockerfile runs the container with
  ORCHESTRATOR_TRANSPORT=streamable-http, ORCHESTRATOR_HTTP_HOST=0.0.0.0,
  ORCHESTRATOR_HTTP_PORT=8100. But config.OrchestratorSettings no longer defines
  http_host/http_port/http_allowed_hosts (extra="ignore" silently drops those env
  vars), and main() passes no bind address — so mcp.run("streamable-http") binds
  FastMCP's default (127.0.0.1:8000), not 0.0.0.0:8100, and re-enables the MCP SDK's
  DNS-rebinding guard. The gateway (GATEWAY_ORCHESTRATOR_MODE=http,
  GATEWAY_ORCHESTRATOR_MCP_URL=http://mcp:8100/mcp) fails every connect attempt →
  orchestrator_client returns ok=False, error="... All connection attempts failed"
  → chat router responds 502. This is the reported production failure. Breaks A1
  (gateway path) and deviates from PLAN v2.

### Routing
Single blocking issue, type=logic → route to Executor (bump exec_version).
Recorded in STATE.open_issues.

## v2 — exec_version=3 — PASS

### Checks
- V1 resolved: `main()` branches to `_run_http()` for http/streamable-http and
  binds uvicorn to `http_host:http_port`; `_NormalizeHostMiddleware`,
  `_disable_sdk_rebinding_protection`, `_extend_fastmcp_guard_hosts` restored
  (PLAN v2 line 57 satisfied).
- config: `http_host`/`http_port`/`http_allowed_hosts` present; Dockerfile
  ORCHESTRATOR_HTTP_HOST=0.0.0.0 / ORCHESTRATOR_HTTP_PORT=8100 /
  ORCHESTRATOR_TRANSPORT=streamable-http now bind through env_prefix ORCHESTRATOR_.
- A1 gateway contract: PASS — orchestrate / delete_thread tool signatures unchanged;
  server reachable at http://mcp:8100/mcp, so the gateway connect (and the reported
  502) is resolved.
- A5 byte-compile: PASS (compileall clean across master_orchestrator).
- open_issues: empty.

Result: PASS. stage -> VALIDATED -> DONE.
