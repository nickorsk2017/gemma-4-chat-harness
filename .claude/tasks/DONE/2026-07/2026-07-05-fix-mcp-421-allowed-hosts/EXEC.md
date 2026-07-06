# EXEC — 2026-07-05-fix-mcp-421-allowed-hosts

## v1 (implements PLAN v1 + one hardening step)

### Changes
1. `config.py` — `http_allowed_hosts` (default ["mcp", "mcp:8100"], env
   ORCHESTRATOR_HTTP_ALLOWED_HOSTS).
2. `main.py`:
   - `_run_http`: try `mcp.http_app(allowed_hosts=..., middleware=...)`; TypeError
     -> fallback to plain call (older fastmcp).
   - `_extend_fastmcp_guard_hosts()` (hardening beyond plan step 2): extends
     `fastmcp.server.http.DEFAULT_HOSTS` with the configured hosts — guarantees
     fastmcp 3.4.3's own guard admits `mcp:8100` even if its `http_app` lacks the
     kwarg; idempotent; no-op when the attribute/module is absent.
   - Previous layers kept (SDK patch, Host normalizer) for 2.x installs.

### Verification (sandbox)
- py_compile clean.
- Stubbed-module test: DEFAULT_HOSTS extended exactly once, idempotent, safe
  no-op without the attribute.
- A1 runtime on host: `docker compose up -d --build mcp`.
