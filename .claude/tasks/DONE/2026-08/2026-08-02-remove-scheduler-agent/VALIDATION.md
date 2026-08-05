# VALIDATION — 2026-08-02-remove-scheduler-agent

## v1

result: PASS
issues: []

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1 | `mcp/` = agent_core, doc_analyzer, image_analyzer, master_orchestrator, web_agent + files; `_to_delete/scheduler_agent/` holds 52 files incl. db/ schemas/ tools/ prompts/ services/ | PASS |
| A2 | `git grep -ni schedul` excluding `frontend/pnpm-lock.yaml` and `.claude/tasks` -> 0 hits | PASS |
| A3 | `grep -rni schedul mcp backend --exclude-dir=.venv` -> 0 hits | PASS |
| A4 | `config.py` parses (ast); registry = web_agent, doc_analyzer, image_analyzer | PASS |
| A5 | repo-wide grep for `SCHEDULER_AGENT_DATABASE_URL` (excl. .git/.venv/_to_delete/task dir) -> 0 hits; compose `mcp.environment` keys carry no scheduler var | PASS |
| A6 | `site-packages/scheduler_agent*` and `bin/scheduler-agent` gone (only unrelated `apscheduler` dep remains, out of scope per PLAN); all three under `_to_delete/venv-leftovers/` | PASS |
| A7 | `drop_scheduler_tables.sql` present; drops `apscheduler_jobs` + `events` in a transaction, carries the `pg_dump` backup line, not executed | PASS |

### Regression checks beyond acceptance
- K4 (Makefile continuations): `make -n dev-install-mcp` exits 0; both edited recipes end on a
  non-continued line (`dev` ends at LANGSMITH block, `run-mcp` at `$(MCP_PY) -m master_orchestrator.main`).
- `docker-compose.yml` parses as YAML; `mcp/pyproject.toml` parses as TOML with deps and
  `[tool.uv.sources]` in 1:1 correspondence (5 entries each, no dangling source).
- `mcp/.env.example` keeps a well-formed section sequence (orchestrator -> LangSmith); no
  orphaned comment left behind.
- `mcp/README.md` both tables keep header/separator/row alignment after row removal.

### Limitation (non-blocking)
Runtime import smoke test of the orchestrator was NOT possible: `mcp/.venv/bin/python3.14`
symlinks to a macOS framework path unreachable from this working session. Verification of
A4 is therefore static (ast parse + registry read), not an executed import. The removal is
one dict entry in a config-driven registry with no other reference in the tree (A2/A3), so
the residual risk is low, but an `import master_orchestrator.config` on the Engineer's own
machine is the cheap confirmation.
