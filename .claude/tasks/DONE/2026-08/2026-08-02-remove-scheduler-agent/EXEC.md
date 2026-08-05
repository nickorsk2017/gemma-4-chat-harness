# EXEC — 2026-08-02-remove-scheduler-agent

## v1

Executed P1-P8 in plan order. No deviation from PLAN.md v1; no re-planning needed.

### Changed files
| File | Change | Plan step |
|---|---|---|
| `mcp/scheduler_agent/` | moved to `_to_delete/scheduler_agent/` (18 files, untracked) | P1 |
| `mcp/.venv/.../site-packages/scheduler_agent`, `scheduler_agent-0.1.0.dist-info`, `bin/scheduler-agent` | moved to `_to_delete/venv-leftovers/` | P2 |
| `mcp/master_orchestrator/config.py` | -1 line: `DEFAULT_SUBAGENTS["scheduler_agent"]` | P3 |
| `mcp/pyproject.toml` | -2 lines (dep, `[tool.uv.sources]` path) + install-order comment | P4 |
| `mcp/Dockerfile` | install list + "four sub-agents" -> "three sub-agents" | P4 |
| `Makefile` | `dev-install-mcp` install list; -2 `SCHEDULER_AGENT_DATABASE_URL` lines (`dev`, `run-mcp`); postgres comment -> "checkpointer needs it" | P4, P5 |
| `docker-compose.yml` | -2 lines: env var + its comment | P5 |
| `mcp/.env.example` | -5 lines: whole `--- scheduler_agent ---` block | P5 |
| `mcp/README.md` | -2 table rows (agent table, distribution table) | P6 |
| `drop_scheduler_tables.sql` (this task dir) | new — DROP for `events` + `apscheduler_jobs`, NOT executed | P7 |

### Notes
- Edits are anchor-based with hit-count assertions (no VCS restore verbs) per Constraint 2.
  One assertion fired and was correct to fire: the README distribution row contains the
  agent row's pattern as a substring; both rows were then dropped by explicit line match.
- P7 target names confirmed from source before authoring the SQL: `__tablename__ = "events"`
  (`db/models.py:23`) and APScheduler's default `apscheduler_jobs` via `SQLAlchemyJobStore`
  (`services/runtime.py:37`). `status` is a String column — no orphan enum type to drop.
- The LangGraph checkpointer tables share the database but belong to the orchestrator; the
  SQL leaves them alone and says so.
- `apscheduler` stays in `mcp/.venv` as an orphaned transitive dep — out of scope per PLAN.

### Not done (by design)
DB script not executed (R7: Engineer runs it). `_to_delete/` not emptied (R2: Engineer
reviews, then removes). No commit (Constraint 4).
