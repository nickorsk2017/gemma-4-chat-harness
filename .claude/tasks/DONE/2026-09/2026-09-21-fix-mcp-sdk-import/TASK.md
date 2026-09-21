# TASK — 2026-09-21-fix-mcp-sdk-import
owner: Engineer
immutable: true

## Requirements
- R1: The `mcp` container must start. It currently crashes at import time:
  `ImportError: cannot import name 'RequestContext' from 'mcp.shared.context'`
  raised from `langchain_mcp_adapters/callbacks.py` via
  `master_orchestrator/services/subagents.py`.
- R2: Resolve the dependency conflict at its root: `fastmcp>=2.0.0` is unbounded and
  resolves to fastmcp 4.x, which requires `mcp>=2.0.0`; mcp 2.x removed
  `mcp.shared.context.RequestContext`, while `langchain-mcp-adapters` requires
  `mcp<2.0.0`. Pins must make the resolution deterministic across the whole mcp fleet.
- R3: No source change to `master_orchestrator` import sites; this is a dependency
  boundary problem, not a code problem.

## Acceptance
- A1: `mcp/*/pyproject.toml` declare bounded, mutually compatible `fastmcp` and `mcp`
  constraints such that a clean resolution selects mcp 1.x.
- A2: A clean dependency resolution of the mcp fleet succeeds with no conflict and
  `import langchain_mcp_adapters.client` works.
- A3: The `mcp` service starts without the ImportError.

## Constraints
- Frameworks are pinned to their latest stable versions compatible with the constraint
  above (fastmcp 3.x line, mcp 1.x line).
- No `--no-deps`, no vendoring, no monkey-patching of the mcp SDK.
