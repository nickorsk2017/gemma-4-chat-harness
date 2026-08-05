# TASK — 2026-08-02-dev-stop-port-sweep
owner: Engineer
immutable: true

## Requirements
- R1: `make dev-stop` must free the stack's ports, not just kill the PIDs recorded in
  `.dev/pids/*.pid`. Observed failure: the processes actually listening on 8100/8000 were
  orphans absent from the pid files, so `dev-stop` reported success, `dev` then failed to
  bind ("[Errno 48] address already in use"), and the stale old build kept serving.
- R2: After the pid-file kill, each service sweeps its own port: find the listeners, send
  TERM, wait for release, escalate to KILL only if the port is still held.
- R3: Port numbers honour the same overrides as `dev` / `dev-ps` (`MCP_PORT`,
  `BACKEND_PORT`, `FRONTEND_PORT`, root `.env`), never a hardcoded literal.
- R4: If the sweep tool is unavailable, say so and continue — `dev-stop` must not fail.
- R5: Report each action: pid-file kill, orphan TERM/KILL with pid, and a loud warning if
  the port is still held at the end.
- R6: Scope is the root `Makefile` only. `dev-restart` inherits the fix via `dev-stop`.

## Acceptance
- A1: `make -n dev-stop` expands without error; `make dev-stop DEV_DIR=<tmp>` runs green
  against an empty pid dir and prints per-service lines.
- A2: With a live listener on a test port, the target kills it and the port ends free.
- A3: With no listener, the target is a no-op for that port and stays exit 0.
- A4: `make -n dev` and `make -n dev-restart` still expand (no recipe breakage).
- A5: Ports resolve from env: `MCP_PORT=9999 make -n dev-stop` shows 9999, not 8100.

## Constraints
- Follow precedence: `.claude/` harness > root CLAUDE.md.
- Surgical edit; the Makefile carries unrelated uncommitted changes (no VCS restore verbs).
- Tests must not touch the real `.dev/` — it tracks the Engineer's live processes.
- No commit.
