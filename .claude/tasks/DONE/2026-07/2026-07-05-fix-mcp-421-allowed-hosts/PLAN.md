# PLAN — 2026-07-05-fix-mcp-421-allowed-hosts

## v1
1. config.py: `http_allowed_hosts: list[str] = ["mcp", "mcp:8100"]`
   (env ORCHESTRATOR_HTTP_ALLOWED_HOSTS; R2).
2. main.py `_run_http()`: try `mcp.http_app(allowed_hosts=..., middleware=[...])`;
   on TypeError (pre-3.x fastmcp without the kwarg) fall back to the current call
   (R3). Keep `_disable_sdk_rebinding_protection()` + `_NormalizeHostMiddleware`.
3. Verify: py_compile; simulate both branches with stub http_app.
Risk: guard may normalize host patterns (port-insensitive) — passing both "mcp"
and "mcp:8100" covers either convention.
