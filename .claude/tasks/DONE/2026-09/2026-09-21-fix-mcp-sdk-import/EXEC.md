# EXEC — 2026-09-21-fix-mcp-sdk-import

## v1
Implements PLAN v1. Dependency metadata only; no source file changed.

### Files written
- `mcp/agent_core/pyproject.toml` — `fastmcp>=2.0.0,<4.0.0`, added `mcp>=1.24.0,<2.0.0`,
  plus the comment recording why the upper bound exists.
- `mcp/guardrails/pyproject.toml` — same two constraints.
- `mcp/web_agent/pyproject.toml` — same two constraints.
- `mcp/doc_analyzer/pyproject.toml` — same two constraints.
- `mcp/image_analyzer/pyproject.toml` — same two constraints.
- `mcp/master_orchestrator/pyproject.toml` — same two constraints;
  `langchain-mcp-adapters` raised from `>=0.1.0` to `>=0.3.2,<0.4.0`.

### Evidence
- Clean resolution of the fleet's third-party constraint set (uv, python 3.14 target)
  selects `fastmcp==3.4.7`, `fastmcp-slim==3.4.7`, `mcp==1.30.0`,
  `langchain-mcp-adapters==0.3.2`, `langchain-core==1.6.3`. No conflict reported.
- In a clean environment built from the new constraints,
  `import langchain_mcp_adapters.client` succeeds — the previous
  `ImportError: cannot import name 'RequestContext'` is gone.
- fastmcp 3.x API surfaces used by the fleet are present: `fastmcp.FastMCP`,
  `fastmcp.Client`, `fastmcp.server.http`, `mcp.server.transport_security`.

### Not done
- Image rebuild and container start are Validator steps.
