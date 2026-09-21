# TASK — 2026-09-21-ci-install-pytest
owner: Engineer
immutable: true

## Requirements
- R1: CI job `gate` in `.github/workflows/harness-gate.yml` fails at "Run backend pytest" with exit 127 because `backend/.venv/bin/pytest` does not exist: `make dev-install-backend` installs `./backend[sqlite]` without the `dev` extra, and `make dev-install-mcp` installs no test deps either.
- R2: Install pytest and pytest-asyncio into `backend/.venv` and `mcp/.venv` in the workflow, after the install steps and before the pytest steps.

## Acceptance
- A1: `backend/.venv/bin/pytest` and `mcp/.venv/bin/pytest` exist in CI before the test steps run.
- A2: Only `.github/workflows/harness-gate.yml` is changed; Makefile unchanged.

## Constraints
- Version pins match the `dev` extras: pytest>=8.0.0, pytest-asyncio>=0.23.0.
