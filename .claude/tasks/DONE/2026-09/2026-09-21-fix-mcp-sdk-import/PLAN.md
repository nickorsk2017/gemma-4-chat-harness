# PLAN — 2026-09-21-fix-mcp-sdk-import

## v1

### Root cause
Two published constraint sets are mutually exclusive on the `mcp` SDK major version:

- `fastmcp` 4.x (`fastmcp-slim[client,server]`) requires `mcp>=2.0.0,<3.0.0`.
- `langchain-mcp-adapters` 0.3.x requires `mcp>=1.24.0,<2.0.0`.

`mcp` 2.x rewrote `mcp/shared/context.py`: the module now exports `BaseContext` only,
and `RequestContext` is gone. `langchain_mcp_adapters/callbacks.py` imports
`RequestContext` from that module, so the import fails at container boot.

Every `mcp/*/pyproject.toml` declares `fastmcp>=2.0.0` with no upper bound, so the
image build resolves fastmcp 4.x and therefore mcp 2.x. The Dockerfile installs the
distributions with sequential `pip install` calls, so `agent_core` (installed first)
fixes the fastmcp/mcp versions for the whole image; a pin present only in
`master_orchestrator` would arrive too late. The pin must therefore be uniform
across every distribution in the fleet.

This is a dependency-boundary defect: no `master_orchestrator` source file is wrong.

### Decision
Hold the fleet on the mcp 1.x SDK line — the line `langchain-mcp-adapters` supports —
by bounding fastmcp below its 4.x major and declaring the `mcp` bound explicitly, so
the constraint is stated at the point it matters rather than inherited implicitly from
fastmcp's own metadata.

Rejected alternatives:
- Upgrade to mcp 2.x and drop `langchain-mcp-adapters` (rewrite `SubagentToolset`
  against the fastmcp client): a cross-cutting rewrite of the sub-agent transport for
  no functional gain; out of scope for this task's acceptance criteria.
- Pin only `master_orchestrator`: ineffective, see the sequential-install note above.
- `pip install --no-deps` or vendoring the SDK: forbidden by TASK constraints.

### Change set
1. `mcp/agent_core/pyproject.toml` — bound `fastmcp` to `>=2.0.0,<4.0.0`; add
   `mcp>=1.24.0,<2.0.0`.
2. `mcp/guardrails/pyproject.toml` — same two constraints.
3. `mcp/web_agent/pyproject.toml` — same two constraints.
4. `mcp/doc_analyzer/pyproject.toml` — same two constraints.
5. `mcp/image_analyzer/pyproject.toml` — same two constraints.
6. `mcp/master_orchestrator/pyproject.toml` — same two constraints, plus raise
   `langchain-mcp-adapters` from `>=0.1.0` to `>=0.3.2,<0.4.0` so the lower bound
   matches the release whose metadata carries the `mcp<2.0.0` constraint.
7. Add a short comment above the constraint in `mcp/agent_core/pyproject.toml` only,
   recording why the upper bound exists, so a future bump does not silently reopen the
   conflict. The other five files carry the pin without duplicated prose.

No source file under `mcp/*/` is edited.

### Validation strategy
- Resolution check: resolve the fleet's dependencies clean and assert the selected
  `mcp` version is 1.x and `fastmcp` is 3.x.
- Import check: `import langchain_mcp_adapters.client` and
  `master_orchestrator.services.subagents` succeed.
- Service check: the `mcp` container boots past the previous traceback.

### Risks
- fastmcp 3.x vs 2.x API drift: the agents use the `FastMCP` server surface, which is
  stable across the 2.x -> 3.x boundary; the import check plus the mcp pytest suite
  cover it. If a 3.x incompatibility surfaces, the bound narrows to `<3.0.0` — the
  mcp 1.x floor still holds.
