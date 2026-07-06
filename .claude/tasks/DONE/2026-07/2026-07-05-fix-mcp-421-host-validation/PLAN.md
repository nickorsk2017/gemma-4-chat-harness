# PLAN — 2026-07-05-fix-mcp-421-host-validation

## v1

### Strategy
The 421 is raised by the MCP SDK's transport-security middleware comparing the
incoming `Host` header against a localhost-only default allowlist. fastmcp does not
expose that middleware's settings through a stable public kwarg (R2), so the fix
normalizes the `Host` header *before* the SDK sees it, using fastmcp's documented
extension point: `mcp.http_app(middleware=[...])` (stable since 2.3.2). A tiny pure
ASGI middleware rewrites `Host` to `localhost:<port>`; server-to-server calls carry
no `Origin` header, so no other check is affected. The app is served with uvicorn
(already a fastmcp dependency). Justified because the server is reachable only on
the internal docker network (R4) — trust is enforced by network isolation, not by
Host-header matching.

### Impact map
1. `mcp/master_orchestrator/config.py` — add `http_host: str = "0.0.0.0"`,
   `http_port: int = 8100` (env `ORCHESTRATOR_HTTP_HOST/PORT`; config, not constants).
2. `mcp/master_orchestrator/main.py` —
   - ASGI middleware class that replaces the `Host` header on http scopes;
   - `main()` branches on `settings.transport`: stdio -> `mcp.run(...)` unchanged
     (R3); `http`/`streamable-http` -> `uvicorn.run(mcp.http_app(middleware=[...]),
     host=settings.http_host, port=settings.http_port)`;
   - docstring carries the security rationale (R4).
3. `mcp/Dockerfile` — CMD becomes `python -m master_orchestrator.main` with
   `ORCHESTRATOR_TRANSPORT=streamable-http` (env keeps transport a runtime choice).
4. `docker-compose.yml` — no change required (port mapping already 8100); verify only.

### Risks
- fastmcp `http_app()` default path is `/mcp` — matches the gateway URL; assert in
  validation.
- Rewritten host must include a port, since allowlist entries are `host:port`
  patterns — use `localhost:<http_port>`.
- If a future fastmcp exposes transport security settings, this middleware stays
  harmless (it runs before validation and only touches `Host`).

### Sequencing
1 -> 2 -> 3 -> py_compile + static review (no Python deps/PyPI in sandbox; runtime
check happens on the host via `docker compose up -d --build mcp`).
