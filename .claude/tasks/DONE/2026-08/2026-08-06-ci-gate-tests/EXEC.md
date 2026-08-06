# EXEC — 2026-08-06-ci-gate-tests

## v1 (per PLAN.md P1-P5)

### Changed files
- `.github/workflows/harness-gate.yml` — P1-P3: added `pnpm/action-setup@v4` +
  `actions/setup-node@v4` (Node 22, pnpm cache keyed on `frontend/pnpm-lock.yaml`);
  added `Install backend deps` / `Install mcp deps` / `Install frontend deps` steps
  using existing `make dev-install-backend` / `dev-install-mcp` / `dev-install-frontend`
  targets; added `Run backend pytest` / `Run mcp pytest` / `Run frontend jest` steps
  as separate named steps. `Enforce artifact-harness invariants` (`ci_check.py`)
  kept as the first step (P4, fail fast). No `continue-on-error`, no exit-code
  swallowing — each step gates the job by default GitHub Actions behavior.
- `.claude/CLAUDE.md` — P5: added a paragraph after the Commit Gate section stating
  `harness-gate.yml` also runs backend pytest / mcp pytest / frontend jest as
  independent steps, and that this is separate from `ci_check.py`'s harness-only
  scope.

### Notes / deviations from plan
- Test invocation uses the venv binaries directly (`backend/.venv/bin/pytest backend`,
  `mcp/.venv/bin/pytest mcp`) rather than a `make test` target, since no such target
  existed in the Makefile and adding one was not in PLAN.md scope (Makefile changes
  weren't called out as an impacted file).
- Did not add a Makefile `test` target — out of PLAN.md's file/impact map, which
  named the workflow file and CLAUDE.md docs only.
- `backend/__tests__/test_rate_limit.py` was not modified or excluded; not
  independently confirmed deterministic under CI load in this pass — flagging per
  PLAN.md risk note. No open_issue raised (not observed failing, just not verified
  timing-safe under CI-shared runners); Engineer/Validator may want to watch first
  CI run.
- No secrets/service containers were added; if `test_rate_limit.py` or any other
  test requires `GEMMA_API_KEY` / Postgres per the Makefile's `dev` target, first
  CI run will surface it as a failure rather than being silently skipped, per
  PLAN.md R2 (do not hide failures).

### Verification performed
- Confirmed test suites exist and match the steps added: `backend/__tests__/`,
  `mcp/__tests__/` + `mcp/guardrails/__tests__/`, `frontend/__tests__/` (jest via
  `frontend/package.json`'s existing `"test": "jest"` script).
- Confirmed `frontend/pnpm-lock.yaml` exists (required for the setup-node pnpm
  cache key).
- Did not execute the full CI workflow locally (no GitHub Actions runner in this
  sandbox); YAML structure reviewed by eye for step ordering and indentation.
