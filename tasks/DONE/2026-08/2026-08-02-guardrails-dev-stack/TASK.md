# TASK — 2026-08-02-guardrails-dev-stack
owner: Engineer
immutable: true

## Context
`make dev` (docker-free stack) starts mcp + backend + frontend as host processes and
postgres as a container. It never starts `guardrails` and never sets `GUARDRAILS_URL`,
so `agent_core.guardrails._base_url()` falls back to `http://guardrails:8200` — a name
that resolves only inside the Compose network. `check_input` is fail-closed (TASK R8),
so every turn is rejected with "the safety gate is unavailable; the request cannot be
processed". Observed in `.dev/logs/mcp.log`:
`guardrails unreachable at /v1/check/input: [Errno 8] nodename nor servname provided`.
`make up` (Compose) is unaffected. `.env.example` documents no guardrails variables.

## Requirements
- R1: The docker-free stack (`make dev`) MUST bring up a reachable guardrails gate before
  the mcp orchestrator starts serving, so `check_input` succeeds on a clean checkout.
- R2: The mcp process started by `make dev` and by `make run-mcp` MUST receive a
  `GUARDRAILS_URL` that is resolvable from the host (not the Compose-internal hostname).
- R3: `make dev-stop` / `dev-restart` / `dev-ps` / `dev-clean` MUST cover guardrails
  consistently with the other services (no orphaned process or container).
- R4: `.env.example` MUST document every guardrails variable the two stacks read
  (`GUARDRAILS_URL`, `GUARDRAILS_TIMEOUT_S`, and the judge/review vars already consumed by
  docker-compose.yml), with the host-vs-compose distinction stated.
- R5: The Compose stack (`make up`) MUST keep working unchanged; no regression in
  service startup order or the guardrails healthcheck dependency.
- R6: No change to the fail-closed/fail-open policy in `mcp/agent_core/guardrails.py`.
  This task is environment wiring only.

## Acceptance
- A1: On a clean checkout with `.env` present, `make dev` then a chat turn returns a real
  answer; `.dev/logs/mcp.log` contains no "guardrails unreachable" line.
- A2: `make dev-ps` reports guardrails state alongside mcp/backend/frontend.
- A3: `make dev-stop` leaves no listener on the guardrails port; `make dev-clean` removes
  any guardrails artefacts it created.
- A4: `make up` still starts the full stack and a chat turn still passes the gate.
- A5: `.env.example` lists the guardrails variables; a reader can start either stack from
  it without editing the Makefile.
- A6: `git diff` touches no file under `mcp/agent_core/`.

## Constraints
- Frameworks stay pinned to current versions; no new runtime dependency for the gate client.
- Decide and record in PLAN.md whether the docker-free stack runs guardrails as a host
  process (own venv, mirroring mcp/backend) or as a published container (mirroring the
  postgres precedent in `dev-db`). Both satisfy R1; the choice is architectural.
- Guardrails needs postgres for held-for-review cases (`GUARDRAILS_REVIEW_DATABASE_URL`);
  the host variant must use the host-reachable URL, as `DEV_DB_URL` already does.
- Loopback only (`DEV_HOST`), consistent with the rest of the docker-free stack.
