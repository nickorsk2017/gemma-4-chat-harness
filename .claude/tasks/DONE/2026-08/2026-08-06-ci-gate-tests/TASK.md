# TASK — 2026-08-06-ci-gate-tests
owner: Engineer
immutable: true

## Problem
`.github/workflows/harness-gate.yml` only runs `.claude/scripts/ci_check.py`, which
verifies harness state invariants (no ESCALATED task, empty open_issues, DONE=>PASS,
STATE<->artifact consistency). It does not run the project's own test suites
(backend pytest, frontend/mcp jest). A task can reach VALIDATED/DONE and be merged
even though pytest/jest are failing or were never run, because nothing in CI
enforces it.

## Requirements
- R1: CI must run backend pytest (and frontend/mcp jest, if those suites exist and
  are runnable in CI) as a real gate — non-zero exit fails the build.
- R2: The existing `ci_check.py` harness-invariant gate must keep running and keep
  gating independently (do not conflate "harness is well-formed" with "tests pass"
  into one check).
- R3: `.claude/CLAUDE.md` (Commit Gate / CI section) and any subsystem CLAUDE.md
  that documents CI must be updated to describe the new test gate.

## Acceptance
- A1: CI workflow fails the build when backend pytest fails.
- A2: CI workflow fails the build when frontend/mcp jest fails (for whichever of
  those suites actually exist and are runnable in the CI environment).
- A3: `ci_check.py` / harness-gate check still runs and still independently gates
  the build.
- A4: Docs updated to describe the new test gate.

## Constraints
- Out of scope: writing new tests, fixing currently-failing tests (route as a
  separate task if discovered), changing the harness state machine.
