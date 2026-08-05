# PLAN — 2026-08-02-guardrails-dev-stack

## v1

### Observed state (working tree, uncommitted)
The Makefile already carries a partial, off-harness implementation: `dev` starts a
guardrails host process on `DEV_GUARDRAILS_PORT` with a TCP readiness wait and exports
`GUARDRAILS_URL`/`GUARDRAILS_TIMEOUT_S` into the mcp process; `DEV_SERVICES` and
`dev-stop` list guardrails. The task is therefore still live but reduced to a delta:
R1 and the `dev` half of R2 are satisfied; R2 (`run-mcp`), R3 (`dev-ps`) and R4 are not.
The plan below covers the delta only; the existing `dev` block is treated as given and
is not re-derived.

### Decisions

**D1 — The docker-free stack runs guardrails as a host process in the shared `mcp/.venv`,
not as a published container.** The Constraints leave this open; it is settled by the
dependency shape, not by convenience. `dev-db` uses a container because postgres is a
third-party image with no source in this repo and no import relationship to our code.
guardrails is the opposite on both counts: it is first-party source under `mcp/guardrails`
that imports `agent_core`, and `dev-install-mcp` already pip-installs it into `mcp/.venv`
alongside the other agents. A container variant would require building
`mcp/guardrails/Dockerfile` on every `make dev`, which reintroduces the docker build step
the docker-free stack exists to avoid, and would leave edits to `agent_core` invisible
until a rebuild — the exact inconsistency the host-process model for mcp/backend prevents.
Consequence: guardrails is lifecycle-identical to mcp/backend (pid file, log file,
`dev_kill`), and `dev-clean` needs no guardrails-specific artefact removal beyond `.dev/`
and the venv it already deletes.

**D2 — `run-mcp` must export the same gate variables as `dev`, sourced from one place.**
R2 names `run-mcp` explicitly, and it is the debugging entry point: a foreground mcp that
silently falls back to the Compose hostname reproduces the original failure precisely when
the developer is trying to observe it. But `run-mcp` starts no guardrails of its own — it
is a single-service target by contract, and starting a second background process from it
would break that contract and leak a process past Ctrl-C. So `run-mcp` points at whatever
gate is already listening (`make dev` or `make run-guardrails`), and the port/URL
expression is factored into a Makefile variable shared by both targets rather than
duplicated. The duplicated literal is the defect risk here, not the missing line.

**D2a — Consequence: a standalone way to start only the gate is required.** `run-mcp` now
depends on a listener it does not create. Without a single-service target for guardrails,
the documented debugging flow is "run the full `dev` stack, then kill three of four
processes". Add the foreground sibling (`run-guardrails`) next to `run-mcp`/`run-backend`;
it is the same shape as the block already inside `dev`.

**D3 — `dev-ps` gains a `guardrails)` branch; the missing branch is a latent bug, not a
cosmetic one.** The `case` in `dev-ps` has no arm for guardrails even though `DEV_SERVICES`
lists it, so `port` retains the previous loop iteration's value — the row prints a wrong
port, not an empty one. A2 requires guardrails be *reported*; a wrong port is worse than
no row. Fix the case, not the service list.

**D4 — `.env.example` documents the gate variables in one block, split by which stack reads
them.** R4's "host-vs-compose distinction" is the substance: `GUARDRAILS_URL` is set by
`docker-compose.yml` and by the Makefile and must NOT be set by the reader (a value copied
from `.env` overrides both stacks and breaks whichever one it does not match), whereas
`GUARDRAILS_PORT`, the judge budget and the retry ladder are reader-tunable in both. State
that asymmetry explicitly; listing the names alone satisfies A5 literally and misleads.

**D5 — The `GUARDRAILS_REVIEW_DATABASE_URL` constraint is stale and must not be
implemented.** TASK Constraints require the host variant to point a review database at the
host-reachable postgres URL. No such setting exists: `guardrails/config.py` has no review or
database field, and its own comment records that the medical path answers with a disclaimer
and there is "no held turn and no moderator queue". Wiring a variable nothing reads would
add a documented knob with no effect — the opposite of R4's intent. R4's parenthetical
"judge/review vars already consumed by docker-compose.yml" resolves to the judge vars only
(`GUARDRAILS_JUDGE_TIMEOUT_S`, `GUARDRAILS_JUDGE_MAX_CHARS`, `GUARDRAILS_MEDICAL_DISCLAIMER`).
Since TASK.md is immutable and Engineer-owned, this is flagged for the approval gate rather
than silently dropped; if the Engineer disagrees, the task reroutes with a `requirement`
issue. Consequence if accepted: guardrails needs no postgres at all in the docker-free
stack, so it may start before `dev-db` and its readiness wait is the only ordering
constraint (which `dev` already honours).

**D6 — The guardrails host process gets the judge variables `dev` currently omits.** The
`dev` block passes only transport/host/port/key, so a developer who tunes
`GUARDRAILS_JUDGE_TIMEOUT_S` in `.env` sees it apply under `make up` and vanish under
`make dev`. Documenting them per D4 while only one stack honours them is a contradiction
inside this task, not a separate improvement.

### Impact map
- `Makefile` — shared gate URL/port variable; `run-mcp` env; new `run-guardrails`;
  `dev-ps` case arm; judge vars in the `dev` guardrails block. No change to `dev-stop`,
  `dev-restart`, `dev-clean` (D1 makes them already correct).
- `.env.example` — one new documented block (D4).
- Nothing else. A6 holds trivially: no file under `mcp/` is touched, which also satisfies R6.
- `docker-compose.yml` untouched -> R5 holds by construction.

### Risks
- **RK1** — `dev` and `run-mcp` drifting apart again. Mitigated by D2's single shared
  expression; a reviewer checks there is exactly one place the host gate URL is spelled.
- **RK2** — a reader sets `GUARDRAILS_URL` in `.env` after reading the new block and breaks
  `make up`. This is the failure D4 is written to prevent; the wording is the mitigation and
  should be checked as such.
- **RK3** — A1 ("clean checkout, no 'guardrails unreachable' line") cannot be asserted from
  the working tree alone, since the fix under test is uncommitted. Validation must run the
  stack, not read the diff.

### Steps
1. Factor the host gate port/URL into a shared Makefile variable; repoint the `dev` block at it. (R2, RK1)
2. Add the judge vars to the `dev` guardrails block. (D6, R4)
3. Add `run-guardrails`; export the gate variables in `run-mcp`. (R2, D2, D2a)
4. Add the `guardrails)` arm to the `dev-ps` case. (R3, A2)
5. Document the gate block in `.env.example` with the host-vs-compose asymmetry. (R4, A5)
6. Verify by running: `make dev` + one chat turn (A1), `make dev-ps` (A2), `make dev-stop`
   + port check (A3), `make up` + one chat turn (A4), `git diff --stat` for A6.

### Open question for the approval gate
D5 contradicts a TASK Constraint. Engineer confirms the drop, or reroutes with a
`requirement` issue to amend TASK.md.
