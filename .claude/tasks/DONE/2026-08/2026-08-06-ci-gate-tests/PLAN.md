# PLAN — 2026-08-06-ci-gate-tests

## v1

### Architecture decision
Keep `ci_check.py` (harness invariants) and test execution as two independent
gate steps in the same workflow file, not merged into one script/job. Rationale:
different failure domains (process integrity vs code correctness), different
owners of the two checks over time, and `ci_check.py`'s contract (exit 1 on
harness violation) must not be diluted by unrelated test-runner exit codes.
Both steps run in the same `gate` job so a single required check
(`harness-gate`) still covers the branch — no new required-check config needed
in repo branch protection.

### Impact map
- `.github/workflows/harness-gate.yml` — add steps: install backend deps, install
  mcp deps, install frontend deps, run backend pytest, run mcp pytest, run
  frontend jest. Existing `ci_check.py` step stays, unchanged, and stays as its
  own step (order: harness check first — fail fast on process violations before
  paying for dependency installs/test runs).
- Dependency install: reuse existing `Makefile` targets (`dev-install-backend`,
  `dev-install-mcp`, `dev-install-frontend`) rather than hand-rolled pip/pnpm
  calls in the workflow, so CI and local dev install the same way and drift is
  caught centrally in the Makefile.
- Test invocation: backend via its own `.venv` (`backend/.venv/bin/pytest` or
  `make`-driven equivalent), mcp via its own `.venv` per the same pattern,
  frontend via `pnpm --dir frontend test` (maps to `package.json`'s existing
  `"test": "jest"` script). No new test files; this only wires up existing
  suites (`backend/__tests__`, `mcp/__tests__` + `mcp/guardrails/__tests__`,
  `frontend/__tests__`).
- Runtime deps for CI: Python 3.14 (already provisioned in the workflow via
  `actions/setup-python@v5`), plus Node/pnpm for the frontend step — the
  workflow currently only sets up Python, so add Node + pnpm setup
  (`actions/setup-node@v4`, `corepack enable` or `pnpm/action-setup@v4`).
- `backend/__tests__/test_rate_limit.py` and any test requiring external
  services (DB, GEMMA_API_KEY per Makefile's `dev` target) must be checked by
  Executor for CI-runnability; if a suite needs infra unavailable in CI
  (service containers, secrets), Executor documents that as a known gap in
  EXEC.md rather than silently skipping it — flag for Engineer review, do not
  invent mocking strategy (that's a logic decision within Executor's existing
  scope only if trivial, else re-route).
- Docs: `.claude/CLAUDE.md` Commit Gate section — add one line noting CI also
  gates on backend pytest / mcp pytest / frontend jest, not just harness
  invariants. `.claude/scripts/ci_check.py` docstring is unaffected (its scope
  is unchanged) but the workflow-level comment/description should say what the
  full gate now covers.

### Sequencing
1. Executor adds Node/pnpm setup steps to `harness-gate.yml` (frontend needs it;
   Python already provisioned).
2. Executor adds three install steps using existing Makefile targets:
   `dev-install-backend`, `dev-install-mcp`, `dev-install-frontend`.
3. Executor adds three test-run steps (backend pytest, mcp pytest, frontend
   jest), each a separate named step so failures are individually attributable
   in the Actions UI.
4. Executor keeps the `ci_check.py` step as step 1 in the job (fail fast, no
   dependency installs paid for on a broken harness).
5. Executor updates `.claude/CLAUDE.md` Commit Gate / CI paragraph to describe
   the expanded gate.
6. Validator confirms: workflow YAML is syntactically valid, all four checks
   (harness + 3 test suites) are present as independent steps under the `gate`
   job, docs updated, and (per constraint) no test files or harness state
   machine logic were touched.

### Risks
- CI runtime cost/time increases (three dependency installs + three test runs
  per push/PR). Accepted trade-off per TASK.md goal; not a blocker.
- If any existing suite is currently failing, this change will turn currently-
  green CI red. That is the intended effect (TASK.md goal), but Executor must
  surface it explicitly in EXEC.md rather than silently adjusting the gate to
  hide it (e.g., no `continue-on-error: true`, no swallowing exit codes).
- `backend/__tests__/test_rate_limit.py` name suggests timing-sensitive test;
  flaky-under-CI risk. If Executor finds it non-deterministic, note as an
  open_issue (type: logic) rather than disabling it unilaterally.
