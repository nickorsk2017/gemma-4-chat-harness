# VALIDATION — 2026-08-02-dev-stop-port-sweep

## v1

result: PASS
issues: []

### Acceptance
| Id | Evidence | Verdict |
|---|---|---|
| A1 | `make -n dev-stop` exit 0; `make dev-stop DEV_DIR=/tmp/devtest` exit 0 on an empty pid dir, three per-service lines printed | PASS |
| A2 | decoy listener on 9997: `MCP_PORT=9997 make dev-stop` -> "still held by 7 — sending TERM" -> "port 9997 free"; port confirmed free after | PASS |
| A3 | same target with no listener: no sweep output, exit 0 | PASS |
| A4 | `make -n dev` and `make -n dev-restart` exit 0 | PASS |
| A5 | runtime override honoured: MCP_PORT=9997/9998 swept those ports; with no override the run reports 8100/8000/3000 | PASS |

### Extra checks
- KILL escalation: a listener with SIGTERM set to SIG_IGN on 9998 survived TERM, was reported
  as "survived TERM — sending KILL", died, port freed. Elapsed ~7s — the 5x1s poll budget
  behaves as designed and does not hang.
- R4 branch exercised for real: `PATH=/tmp/nolsof2` (no `lsof`) -> "lsof not found — port N
  not swept" for all three services, exit 0. A separate run with an always-failing `lsof`
  stub also stayed exit 0 (empty holders, no sweep).
- Pid-file path intact: `backend.pid` pointing at a live `sleep` -> "stopped backend (pid 32)",
  process gone, pid file removed.
- Tests ran against `DEV_DIR=/tmp/devtest`; the real `.dev/` was never touched (Constraint 3).

### Note (not an issue)
The sweep kills whatever holds the port, which on a dev box may be an unrelated process
(3000 is a common default). That is the requested behaviour (R1/R2), mitigated by R5: every
kill prints service, port and pid before acting.
