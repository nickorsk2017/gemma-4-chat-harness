# TASK — 2026-08-02-remove-scheduler-agent
owner: Engineer
immutable: true

## Requirements
- R1: Remove the scheduling feature from the repository entirely. The `scheduler_agent`
  sub-agent (added by task 2026-07-13-scheduler-agent, extended by
  2026-07-13-scheduler-event-ids) is dropped as a product capability, not merely disabled.
- R2: Delete the package `mcp/scheduler_agent/` (all of db/, schemas/, tools/, prompts/,
  services/, config.py, main.py, pyproject.toml). The folder is UNTRACKED in git, so the
  deletion is not recoverable via VCS: it MUST be moved to `_to_delete/scheduler_agent/`
  rather than unlinked, and the Engineer removes that folder manually after review.
- R3: Unregister the sub-agent from the orchestrator: remove the `scheduler_agent` entry
  from `DEFAULT_SUBAGENTS` in `mcp/master_orchestrator/config.py`. No other orchestrator
  change is in scope — the loop is registry-driven and the orchestrator prompts never
  described the scheduling tool.
- R4: Remove the distribution from every build/install path: `mcp/pyproject.toml`
  (dependency `scheduler-agent`, its `[tool.uv.sources]` path entry, and the install-order
  comment), `mcp/Dockerfile` (pip install list and the "four sub-agents" comment), and the
  `dev-install-mcp` target in the root `Makefile`.
- R5: Remove its runtime configuration: `SCHEDULER_AGENT_DATABASE_URL` from
  `docker-compose.yml` (with its comment), from both invocations in the root `Makefile`
  (the `dev` target and `run-mcp`), and the whole `--- scheduler_agent ---` block from
  `mcp/.env.example`. The Makefile comment naming the "checkpointer/scheduler" reason for
  postgres is updated to reference the checkpointer only.
- R6: Remove both `scheduler_agent` / `scheduler-agent` rows from the agent and
  distribution tables in `mcp/README.md`.
- R7: Drop the feature's storage from Postgres: table `events` (the scheduler's
  source of truth) and APScheduler's jobstore table. Deliver this as a reviewable SQL
  script; the Engineer runs it — the database is not reachable from the working session.
- R8: Leave the closed task archives `.claude/tasks/DONE/2026-07/2026-07-13-scheduler-agent/`
  and `.../2026-07-13-scheduler-event-ids/` untouched. The archive is immutable history.

## Acceptance
- A1: `mcp/scheduler_agent/` no longer exists under `mcp/`; its contents are intact under
  `_to_delete/scheduler_agent/`.
- A2: `git grep -ni schedul` returns no hits outside `frontend/pnpm-lock.yaml` (the
  unrelated React `scheduler` package) and `.claude/tasks/` (this task plus the archive).
- A3: A filesystem grep over `mcp/` and `backend/` (excluding `.venv`) for "schedul"
  returns nothing.
- A4: `mcp/master_orchestrator/config.py` parses and `DEFAULT_SUBAGENTS` holds exactly
  `web_agent`, `doc_analyzer`, `image_analyzer`.
- A5: No file in the repo references `SCHEDULER_AGENT_DATABASE_URL`.
- A6: The stale pip install of the distribution is gone from `mcp/.venv`
  (`site-packages/scheduler_agent`, its `.dist-info`, and `bin/scheduler-agent`), so a
  removed-but-importable package cannot mask a missed reference.
- A7: A SQL script dropping `events` and the APScheduler jobstore table exists and is
  handed to the Engineer, with a `pg_dump` line for taking a backup first.

## Constraints
- Follow precedence: `.claude/` harness > root CLAUDE.md > subsystem mcp/CLAUDE.md.
- The working tree carries unrelated uncommitted modifications in several of the files in
  scope (Makefile, docker-compose.yml, mcp/*, backend/*). Edits MUST be surgical — no
  `git checkout`, `git stash`, or whole-file rewrite may be used to reach the target state.
- Deletions on this machine go through `_to_delete/`; `rm` is unavailable on the mounted
  working tree.
- No commit is part of this task. The Engineer commits after closing it.
