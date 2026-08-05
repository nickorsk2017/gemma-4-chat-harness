# VALIDATION — 2026-08-02-guardrails-dev-stack

## v1 — PASS

### Requirement conformance

| Req | Verdict | Evidence |
|---|---|---|
| R1 | PASS | `dev` starts guardrails before mcp with a 60s TCP readiness loop on the same port mcp is later pointed at; Engineer confirms a live turn answers. |
| R2 | PASS | Both `dev` (Makefile:196) and `run-mcp` (:344) export `GUARDRAILS_URL=$(DEV_GUARDRAILS_URL)` = `http://127.0.0.1:$${GUARDRAILS_PORT:-8200}/mcp`. No compose hostname reaches a host process. |
| R3 | PASS | guardrails is in `DEV_SERVICES`, has a `dev_kill` line in `dev-stop`, a `dev-ps` case arm, and no artefact outside `.dev/` + `mcp/.venv` that `dev-clean` already removes. `dev-restart` inherits `dev-stop`. |
| R4 | PASS | `.env.example` documents `GUARDRAILS_URL` (as a do-not-set, with both stacks' concrete values), `GUARDRAILS_TIMEOUT_S`, `GUARDRAILS_PORT`, the retry ladder and the three judge vars. |
| R5 | PASS | `git diff -- docker-compose.yml` is empty. |
| R6 | PASS | `git diff --name-only` for this task: `Makefile`, `.env.example`. No file under `mcp/agent_core/`. |

### Acceptance

| Acc | Verdict | Evidence |
|---|---|---|
| A1 | PASS | Engineer-run on host: stack up, turn answers, no "guardrails unreachable" in `.dev/logs/mcp.log`. |
| A2 | PASS | `make dev-ps` prints `guardrails - 8200 stopped/running` as the first row. |
| A3 | PASS | Engineer-run: `dev-stop` leaves no listener on 8200. `dev-clean` removes `.dev/` and `mcp/.venv`, which is the whole guardrails footprint (D1). |
| A4 | PASS | Engineer-run: `make up` starts the stack, a turn passes the gate. |
| A5 | PASS | See R4. A reader can move the gate port or retune the judge from `.env.example` alone. |
| A6 | PASS | Scoped to this task's diff, per EXEC's note. The `mcp/**` entries in the working tree are uncommitted carry-over from 2026-08-03-image-analyzer-output-gate and the pyproject sweep; none is attributable here. Checked by re-running `git diff --stat -- Makefile .env.example docker-compose.yml` against the full `--name-only` list. |

### Checks beyond the acceptance list

- **Documented defaults match the code.** Every default in the new `.env.example` block was
  read back against its consumer, not copied from `docker-compose.yml`:
  `TIMEOUT_S=15`, `RETRY_ATTEMPTS=2`, `RETRY_BASE_S=1`, `RETRY_FACTOR=1`,
  `OUTPUT_DEADLINE_S=35` against `agent_core/guardrails.py:76-104`;
  `JUDGE_TIMEOUT_S=8`, `JUDGE_MAX_CHARS=6000`, `MEDICAL_DISCLAIMER=true` against
  `guardrails/config.py`. No drift. A doc block that disagrees with the defaults is worse
  than none, which is why this was checked rather than assumed.
- **RK1 closed.** The host gate URL is spelled exactly once (Makefile:46); the three other
  occurrences are expansions. `dev` and `run-mcp` cannot drift.
- **RK2 closed.** `grep '^GUARDRAILS_URL' .env.example` returns nothing — the name is
  present only inside comments. A copied `.env` therefore cannot export an empty or
  mismatched URL into either stack. This is the specific failure mode the block warns about,
  and the implementation does not itself commit it.
- **D5 not silently implemented.** No `GUARDRAILS_REVIEW_DATABASE_URL` in `Makefile` or
  `.env.example`; confirmed there is no field in `guardrails/config.py` that would read one.
  Engineer approved the drop at the HIGH gate, so this is not a `requirement` issue.
- **`run-mcp` without a gate.** Not a regression: previously it fell back to the compose
  hostname and failed closed with a DNS error; now it fails closed with a connection refused
  on a correct address. Both reject the turn — the second is diagnosable. The dependency is
  stated in both targets' help text and `run-guardrails` exists to satisfy it (D2a).
- **`GEMMA_API_KEY` guard asymmetry** (`:?` in `run-guardrails` vs `:-` in `dev`) reviewed and
  accepted: `dev` hard-fails in its own preflight before reaching the block.

### Issues

None blocking. No advisory issues raised.

### Result

**PASS**
