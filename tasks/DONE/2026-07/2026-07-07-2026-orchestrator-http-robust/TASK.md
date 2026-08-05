# TASK — orchestrator-http-robust
owner: Engineer
immutable: true

## Requirements
- R1: The orchestrator's streamable-HTTP serving path MUST bind reliably and
  MUST NOT crash at startup if the pinned mcp/fastmcp SDK moves the
  transport-security module or changes its signature (root CLAUDE.md tracks
  latest stable). The Host-normalizer middleware is the primary defense; the
  SDK monkey-patch is best-effort.
- R2: Log the bound address at startup so operators can confirm the server is
  listening on 0.0.0.0:8100/mcp.

## Acceptance
- A1: main.py byte-compiles.
- A2: _disable_sdk_rebinding_protection cannot raise out of _run_http (import +
  patch wrapped, failure logged).
- A3: gateway/orchestrator contracts unchanged (scope = main.py only).
