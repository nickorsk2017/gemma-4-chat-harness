# PLAN — 2026-07-07-files-service

## v1

### Architecture decisions
- D1 (R1): introduce `services/files.py` holding a stateless `FileService` with two
  methods — `validate(file)` and `inject(args, file)`. It mirrors the `services/`
  convention (non-tool logic lives here, alongside `memory.py`/`subagents.py`). It
  imports only `agent_core.files.FilePayload` (type) + `master_orchestrator.config`
  (`settings.max_file_bytes`), so no import cycle: `services.orchestrator` ->
  `services.files` -> {`agent_core.files`, `config`}; none imports orchestrator.
- D2 (R1/A3): move the logic verbatim. `validate` keeps the two guards (kind is None ->
  unsupported-type ValueError; decoded size > cap -> `exceeds the N MiB limit` ValueError,
  cap computed as `settings.max_file_bytes // (1024*1024)`). `inject` keeps the
  `args.get("request", args)` + `isinstance(dict)` + `model_dump()` overwrite. Messages
  byte-identical.
- D3 (R2): `Orchestrator` gains an `__init__` that builds one `FileService` (`self._files`)
  — cheap, stateless, and `Orchestrator()` is already constructed per call
  (`tools/start_job.py`). `run` calls `self._files.validate(request.file)`; `_dispatch`
  calls `self._files.inject(args, file)` guarded by the existing
  `call["name"] in loaded.file_tool_names` check (that routing decision stays in the
  orchestrator, not the service). Remove `_validate` and `_inject_file`.
- D4 (boundary): the file-tool membership check (`loaded.file_tool_names`) is dispatch
  routing, not file logic, so it stays in `_dispatch`. The service is unaware of tool
  identity — it only knows how to validate a payload and how to inject one.

### File impact map
| File | Action | Req |
|---|---|---|
| mcp/master_orchestrator/services/files.py | new (`FileService.validate`/`.inject`) | R1 |
| mcp/master_orchestrator/services/orchestrator.py | modify (import+`__init__`+delegate; drop 2 methods) | R2 |

### Steps
- P1 (R1/A1/A3): create `services/files.py` with `FileService`; move validate + inject
  bodies verbatim (same messages, same cap math).
- P2 (R2): in `orchestrator.py` add the import, add `__init__` setting `self._files`,
  replace `self._validate(request)` with `self._files.validate(request.file)`, replace
  `self._inject_file(args, file)` with `self._files.inject(args, file)`, delete the two
  now-dead methods. Keep the `FilePayload` import (still used in `_dispatch` type hint).
- P3 (A2/A3): verify — `grep _validate/_inject_file` in orchestrator is empty; compileall
  clean; AST import-resolution sweep over the two files resolves; diff-check the two error
  strings and cap expression against the pre-change source.

### Risks
- Low. Only risk: a stray reference to the removed methods or a dropped `FilePayload`
  import — P3 grep + compileall are the guards. Live e2e is env-blocked in the sandbox
  (no MCP servers / PyPI), so static evidence is the gate, consistent with prior tasks
  (non-blocking).
