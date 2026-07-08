# PLAN — 2026-07-07-move-memory-to-services

## v1

### Architecture decisions
- D1 (R1): relocate `memory.py` verbatim to `services/memory.py`. It imports only
  `master_orchestrator.config` + stdlib + langgraph, so no import cycle arises under
  `services/` (`services.orchestrator` -> `services.memory` -> `config`).
- D2 (R2): repoint the three references to `master_orchestrator.services.memory`:
  `tools/delete_thread.py` (`from ... import get_store`), `services/orchestrator.py`
  (same), and the `db/__init__.py` module docstring naming the old path. No API rename —
  `get_store`/`CheckpointThreadStore`/`ThreadState` keep their names.

### File impact map
| File | Action | Req |
|---|---|---|
| mcp/master_orchestrator/services/memory.py | new (moved from memory.py, verbatim) | R1 |
| mcp/master_orchestrator/memory.py | delete | R1 |
| mcp/master_orchestrator/tools/delete_thread.py | modify (import path) | R2 |
| mcp/master_orchestrator/services/orchestrator.py | modify (import path) | R2 |
| mcp/master_orchestrator/db/__init__.py | modify (docstring path) | R2 |

### Steps
- P1 (R1): copy `memory.py` -> `services/memory.py` unchanged; delete the original.
- P2 (R2): update the two `from master_orchestrator.memory import get_store` sites and the
  `db/__init__.py` docstring reference.
- P3 (A1-A3): verify — grep shows no `master_orchestrator.memory` refs; compileall clean;
  AST import-resolution sweep passes.

### Risks
- Trivial relocation; only risk is a missed importer — P3 grep is the guard. Env-blocked
  live e2e (no PyPI/langgraph in sandbox) documented as non-blocking, as in the prior task.
