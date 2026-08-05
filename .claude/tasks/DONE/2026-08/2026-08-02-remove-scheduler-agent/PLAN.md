# PLAN — 2026-08-02-remove-scheduler-agent

## v1

### Impact map
| Layer | File | Nature of edit | Reqs |
|---|---|---|---|
| package | `mcp/scheduler_agent/` | move-out (18 files) | R2 |
| wiring | `mcp/master_orchestrator/config.py` | drop 1 registry entry | R3 |
| build | `mcp/pyproject.toml` | drop dep + path source + comment | R4 |
| build | `mcp/Dockerfile` | drop from install list + comment | R4 |
| build | `Makefile` (dev-install-mcp) | drop from install list | R4 |
| runtime cfg | `docker-compose.yml`, `Makefile` x2, `mcp/.env.example` | drop env var + comments | R5 |
| docs | `mcp/README.md` | drop 2 table rows | R6 |
| venv | `mcp/.venv` (site-packages, bin) | move-out stale install | A6 |
| storage | Postgres `events`, APScheduler jobstore | SQL artifact, run by Engineer | R7 |

### Architecture notes
- The orchestrator discovers sub-agent tools live from `settings.subagents` (config-driven,
  not a hardcoded tool list). Deleting the registry entry is therefore the single functional
  cut: nothing else in the loop, the prompt generator, or the file-injection set names the
  scheduler. This is why R3 is one line and no orchestrator behaviour change is in scope.
- Blast radius is zero for the other three sub-agents: agents share only `agent_core`, and
  no agent imports another. The removal cannot regress web/doc/image paths.
- `apscheduler` remains in `mcp/.venv` as an orphaned transitive dependency. It is not
  removed by hand: the venv is a regenerable artifact and `dev-install-mcp` rebuilds it.
  Hand-pruning it risks breaking an unrelated package that also depends on it.

### Risks
| # | Risk | Mitigation |
|---|---|---|
| K1 | The package is untracked in git — deletion is irreversible | Move to `_to_delete/`, never unlink (R2); Engineer reviews before removing |
| K2 | Files in scope carry unrelated uncommitted edits | Anchor-based surgical edits only; no VCS restore verbs (Constraint 3) |
| K3 | Stale site-packages copy keeps `import scheduler_agent` working, hiding a missed reference | Move the installed copy out BEFORE the reference sweep (A6 gates A3) |
| K4 | Makefile line continuations — dropping a `\`-terminated line can silently truncate a recipe | Drop only whole `VAR=... \` lines, never the last line of a block; verify by reading the two recipes after the edit |
| K5 | Dropping `events` is irreversible | SQL carries a `pg_dump` backup line and runs in a transaction (R7); Engineer executes, not the harness |
| K6 | Over-broad text match (`schedul`) hits the unrelated React `scheduler` package and the task archive | Acceptance A2 scopes the sweep by exclusion, archive left intact (R8) |

### Steps
1. Move the package out (R2). Do this first: it makes every remaining reference a hard
   failure rather than a silent success, which is what the later sweep measures.
2. Move the stale venv install out (A6) — same reasoning, one layer down.
3. Cut the registry entry (R3). Functional removal completes here; everything after is
   build/config/docs hygiene.
4. Cut the build paths (R4) — pyproject, Dockerfile, Makefile install list.
5. Cut the runtime config (R5) — compose, both Makefile recipes, .env.example.
6. Cut the docs rows (R6).
7. Author the DROP script (R7) as a deliverable; do not execute — the DB is unreachable
   from the working session and execution is the Engineer's call.
8. Sweep: tracked-file grep (A2), filesystem grep (A3), config parse (A4), env-var grep
   (A5). Steps 1-2 must precede this or the sweep proves nothing.

### Sequencing constraint
Steps 1-2 strictly before step 8. Steps 3-6 are order-independent among themselves but all
precede the sweep. Step 7 is independent of all others.

### Out of scope
Orchestrator loop/prompt changes; the `apscheduler` venv leftover; the DONE task archive
(R8); any commit.
