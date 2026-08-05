# TASK — 2026-07-07-files-service
owner: Engineer
immutable: true

## Requirements
- R1: Extract the attachment-handling logic out of
  `mcp/master_orchestrator/services/orchestrator.py` into a dedicated
  `mcp/master_orchestrator/services/files.py`. This covers exactly the two file
  concerns currently living on `Orchestrator`: attachment validation (`_validate`'s
  file branch — supported kind + size cap) and raw-file injection into a file-tool's
  args (`_inject_file`). Behavior unchanged (pure relocation of logic).
- R2: `Orchestrator` no longer contains `_validate` or `_inject_file`; it delegates to
  the new service. Validation runs once before the tool-calling loop (as today), and
  injection runs inside `_dispatch` for file-tools (as today). The dispatch-time
  decision of *whether* a tool is a file-tool (`loaded.file_tool_names`) stays in the
  orchestrator — the service only validates and injects.

## Acceptance
- A1: `mcp/master_orchestrator/services/files.py` exists and exposes a service with a
  `validate(file)` (raises `ValueError` on unsupported kind / over-cap) and an
  `inject(args, file)` (overwrites the `file` field, no-op when file is None) with the
  same semantics as the removed `Orchestrator._validate`/`_inject_file`.
- A2: `grep -n "_validate\|_inject_file" services/orchestrator.py` returns nothing; the
  orchestrator imports and calls the new service. `python3 -m compileall
  mcp/master_orchestrator` is clean and every `from master_orchestrator.*` import in the
  touched files resolves.
- A3: The error messages and the 15-MiB cap logic are byte-identical to the originals
  (unsupported-type message and `exceeds the N MiB limit` message unchanged).

## Constraints
- Scope: `mcp/master_orchestrator/services/**` only. No dependency, schema, config, or
  gateway changes; no change to `agent_core.files`.
- Follow subsystem rules in `mcp/CLAUDE.md` (all non-tool logic lives under `services/`;
  contracts via Pydantic; config not constants).
