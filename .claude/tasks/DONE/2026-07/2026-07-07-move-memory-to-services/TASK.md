# TASK — 2026-07-07-move-memory-to-services
owner: Engineer
immutable: true

## Requirements
- R1: Move `mcp/master_orchestrator/memory.py` into
  `mcp/master_orchestrator/services/` (as `services/memory.py`), consistent with the
  services restructure — all non-tool logic lives under `services/`. Contents unchanged
  in effect (only the module home changes).
- R2: Update every importer to the new path (`master_orchestrator.services.memory`):
  `tools/delete_thread.py`, `services/orchestrator.py`, and the `db/__init__.py` docstring
  that names the module. No other behavior changes.

## Acceptance
- A1: `mcp/master_orchestrator/memory.py` no longer exists; `services/memory.py` exists
  with the same `get_store` / `CheckpointThreadStore` / `ThreadState` API.
- A2: `grep -rn "master_orchestrator.memory"` across mcp + backend returns nothing (all
  references point at `services.memory`); `python3 -m compileall mcp/master_orchestrator`
  is clean and every `from master_orchestrator.*` import resolves.
- A3: `get_store` behavior and the `delete_thread`/`start_job` tool contracts are
  unchanged (pure relocation).

## Constraints
- Scope: `mcp/master_orchestrator/**` only. No dependency, schema, or gateway changes.
- Follow subsystem rules in `mcp/CLAUDE.md`.
