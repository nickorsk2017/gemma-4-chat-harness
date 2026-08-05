# EXEC — 2026-08-02-guardrails-dev-stack

## v1 — P1-P5 complete, P6 partial (see Verification)

### Changed

| File | Change | Plan step |
|---|---|---|
| `Makefile` | `DEV_GUARDRAILS_PORT_EXPR` / `DEV_GUARDRAILS_URL` next to `DEV_DB_URL`; `dev` repointed at both | P1 |
| `Makefile` | judge vars added to the `dev` guardrails block | P2 |
| `Makefile` | new `run-guardrails`; `GUARDRAILS_URL`/`GUARDRAILS_TIMEOUT_S` added to `run-mcp`; `.PHONY` extended | P3 |
| `Makefile` | `guardrails)` arm added to the `dev-ps` case | P4 |
| `.env.example` | new "Guardrails gate" block | P5 |
| `docker-compose.yml`, `mcp/**` | **untouched** (R5, R6, A6) | — |

### Implementation notes (deviations and judgement calls only)

- **P1, two variables not one.** `dev` and `dev-ps` need the bare port (readiness probe,
  status column), `run-mcp` needs the URL. Deriving the URL from the port expression keeps
  RK1 closed with one source; exporting only the URL would have forced `dev` to parse it back.
- **P1, `dev` keeps its local `guardrails_port` shell var.** It is now assigned *from*
  `DEV_GUARDRAILS_PORT_EXPR` rather than from a duplicated literal. The var itself stays
  because the readiness loop and `GUARDRAILS_HTTP_ALLOWED_HOSTS` reference it three times.
- **P3, `run-guardrails` uses `:?` on `GEMMA_API_KEY`, `dev` uses `:-`.** Deliberate, and it
  matches `run-mcp`: `dev` already hard-fails on a missing key in its preflight, so a second
  check there would be dead code; a foreground single-service target has no preflight.
- **P3, `run-mcp` starts no gate.** Per D2 it points at a listener started elsewhere. The
  `##` help text on both targets states the dependency — that text is the whole mitigation
  for a developer who runs `run-mcp` alone and hits the fail-closed rejection.
- **P5, `GUARDRAILS_URL` is documented but deliberately not present as a key.** Writing
  `GUARDRAILS_URL=` (empty) in `.env.example` would be actively harmful: `LOAD_ENV` exports
  it, so a copied `.env` would push an empty value into both stacks. The block carries the
  name, both concrete values and a DO-NOT-SET banner instead (D4, RK2).
- **P5, retry-ladder vars included though only the orchestrator reads them.** They are
  guardrails-namespaced and consumed by `docker-compose.yml`; splitting them into a
  different block would hide the fact that `GUARDRAILS_TIMEOUT_S` is one rung of that ladder.
- **D5 honoured:** no `GUARDRAILS_REVIEW_DATABASE_URL` anywhere. Engineer confirmed the drop
  at the approval gate; `guardrails/config.py` has no field that would read it.

### Verification

Run in the sandbox (no docker, no venvs — see the gap below):

- `make -n dev-ps` -> `guardrails) port="${GUARDRAILS_PORT:-8200}"` present; `make dev-ps`
  prints `guardrails - 8200 stopped` as the first row. **A2 met.**
- `make -n run-mcp | grep GUARDRAILS` -> `GUARDRAILS_URL="http://127.0.0.1:${GUARDRAILS_PORT:-8200}/mcp"`
  and `GUARDRAILS_TIMEOUT_S`. No compose hostname. **R2 met.**
- `make -n dev | grep GUARDRAILS` -> the same URL plus the three judge vars.
- `make -n run-guardrails` expands cleanly (8 gate vars).
- `git diff` on `docker-compose.yml`: empty. **R5 holds.**

**Gap for the Validator — A1, A3, A4 not executed.** The sandbox has no docker daemon
(`make dev-ps` fails at its trailing `compose ps postgres` with `docker: command not found`)
and no `mcp/.venv`, so no stack can be started here. RK3 already anticipated this: A1/A3/A4
must be run on the host, not read off the diff.

**A6 scoping note.** `git diff --stat` shows changes under `mcp/` — all of them predate this
task (uncommitted work from `2026-08-03-image-analyzer-output-gate` and the pyproject sweep).
This task's own diff is `Makefile` + `.env.example` only. A6 must be judged against this
task's changes, not against the accumulated working tree.
