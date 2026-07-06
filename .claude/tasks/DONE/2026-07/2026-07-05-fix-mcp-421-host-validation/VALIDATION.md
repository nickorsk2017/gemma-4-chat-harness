# VALIDATION — 2026-07-05-fix-mcp-421-host-validation

## v1 (validates EXEC v1 against TASK + PLAN v1)

### Requirement checks
- R1: PASS by construction — the SDK's rebinding check now always sees
  `Host: localhost:8100` (middleware simulation verified rewrite, header
  preservation, scope immutability, lifespan passthrough). Final runtime
  confirmation is A1 on the host.
- R2: PASS — only documented fastmcp API used (`http_app(middleware=[...])`,
  stable since 2.3.2); no version-specific transport-security kwargs.
- R3: PASS — stdio path is byte-identical (`mcp.run(transport=...)`); default
  `ORCHESTRATOR_TRANSPORT` remains "stdio" outside docker.
- R4: PASS — rationale documented in the middleware docstring + Dockerfile.

### Acceptance checks
- A1: HOST-SIDE — requires `docker compose up -d --build mcp` on the user's
  machine (sandbox has no docker/PyPI); expected: /api/chat* answers, no 421/502.
- A2: PASS — `main()` default branch unchanged.
- A3: PASS — py_compile clean; uvicorn + starlette are fastmcp dependencies,
  nothing new added to pyproject.

### Consistency
- Gateway URL `http://mcp:8100/mcp` matches fastmcp's default http path `/mcp`
  and exposed port 8100 — PASS.
- Dockerfile CMD no longer duplicates transport constants in a `python -c`
  one-liner — config stays in env per constraint — PASS.

### Verdict
PASS — no open issues (A1 runtime confirmation delegated to Engineer host run).
