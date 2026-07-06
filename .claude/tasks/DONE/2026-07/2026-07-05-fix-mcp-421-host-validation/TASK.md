# TASK — 2026-07-05-fix-mcp-421-host-validation
owner: Engineer
immutable: true

## Requirements
- R1: In the docker stack, gateway calls to `http://mcp:8100/mcp` MUST succeed.
  Today the orchestrator's streamable-HTTP server rejects them with
  `421 Misdirected Request`: recent MCP python-SDK versions enable DNS-rebinding
  protection whose default allowlist is localhost-only, and `Host: mcp:8100`
  is not on it (deps are unpinned `fastmcp>=2.0.0`, so a rebuild picked this up).
- R2: The fix must not depend on version-specific fastmcp kwargs (installed
  version unknown/floating). Use only documented, stable fastmcp API.
- R3: stdio transport (local dev, gateway default) must remain unchanged.
- R4: Security rationale documented in code: the orchestrator listens only on
  the internal docker network; the gateway is its sole client.

## Acceptance
- A1: `docker compose up -d --build mcp` -> chat message and file upload get
  answers; no 421/502 from `/api/chat*`.
- A2: `python -m master_orchestrator.main` still runs stdio by default.
- A3: All touched Python files compile; no new runtime deps beyond what
  fastmcp already ships (uvicorn is a fastmcp dependency).

## Constraints
- Transport/host/port stay runtime configuration (env/CMD), not constants in
  application logic, consistent with the existing Dockerfile comment.
- mcp/CLAUDE.md subsystem rules apply.
