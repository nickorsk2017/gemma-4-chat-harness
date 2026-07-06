# TASK — 2026-07-05-fix-mcp-421-allowed-hosts
owner: Engineer
immutable: true

## Requirements
- R1: fastmcp 3.4.3 (confirmed in the running container) enforces its OWN request
  guard in fastmcp/server/http.py (`_host_matches` -> 421 "Misdirected Request");
  the MCP-SDK TransportSecurityMiddleware patch from the previous task does not
  apply to this code path. Fix by passing the guard's supported `allowed_hosts`
  parameter through `mcp.http_app(...)` so `Host: mcp:8100` is accepted.
- R2: Allowed hosts must be configuration (env), defaulting to the compose
  service identity: ["mcp", "mcp:8100"].
- R3: Backwards/forwards tolerant: if the installed fastmcp's `http_app` does not
  accept `allowed_hosts` (older 2.x), fall back to the current call; keep the
  existing SDK patch + Host normalizer as defense-in-depth for those versions.
- R4: stdio path untouched.

## Acceptance
- A1: After rebuild: mcp log shows POST /mcp with 2xx, chat answers, no 421.
- A2: py_compile clean; fallback logic simulated (TypeError path).

## Constraints
- Files: mcp/master_orchestrator/main.py, config.py. Rationale documented in code.
