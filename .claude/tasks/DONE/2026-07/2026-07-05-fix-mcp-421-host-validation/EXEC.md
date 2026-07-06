# EXEC — 2026-07-05-fix-mcp-421-host-validation

## v1 (implements PLAN v1)

### Changes
1. `mcp/master_orchestrator/config.py` — `http_host` (default 0.0.0.0) and
   `http_port` (default 8100), env-driven via ORCHESTRATOR_ prefix.
2. `mcp/master_orchestrator/main.py` —
   - `_NormalizeHostMiddleware` (pure ASGI): on http scopes replaces the `Host`
     header with `localhost:<port>`; docstring carries the security rationale
     (internal docker network, gateway is the sole client).
   - `_run_http()`: `uvicorn.run(mcp.http_app(middleware=[Middleware(...)]),
     host=settings.http_host, port=settings.http_port)`; uvicorn/starlette come
     with fastmcp — no new deps.
   - `main()` branches: "http"/"streamable-http" -> `_run_http()`, anything else ->
     unchanged `mcp.run(transport=...)` (stdio default preserved).
3. `mcp/Dockerfile` — CMD is now `python -m master_orchestrator.main` with
   `ORCHESTRATOR_TRANSPORT=streamable-http`, `ORCHESTRATOR_HTTP_HOST/PORT` as ENV
   (runtime configuration stays outside application logic).
4. `docker-compose.yml` — verified, no change needed (8100 mapping + GATEWAY_
   ORCHESTRATOR_MCP_URL=http://mcp:8100/mcp remain correct).

### Verification runs (sandbox)
- `py_compile` on main.py + config.py -> OK.
- Middleware unit simulation (exec'd class, fake ASGI app): Host mcp:8100 ->
  localhost:8100, other headers preserved, original scope not mutated, non-http
  (lifespan) scopes untouched -> OK.
- Runtime check requires the host docker stack (no fastmcp/PyPI in sandbox):
  `docker compose up -d --build mcp`, then send a chat message (A1).
