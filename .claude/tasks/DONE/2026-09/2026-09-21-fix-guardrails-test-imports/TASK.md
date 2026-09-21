# TASK — 2026-09-21-fix-guardrails-test-imports
owner: Engineer
immutable: true

## Requirements
- R1: CI mcp pytest fails at collection: four tests in mcp/guardrails/__tests__ import `guardrails.tests.fixtures.*`, but the package was renamed to `guardrails/__tests__`. Make all CI test suites pass.

## Acceptance
- A1: `pytest mcp` passes with 0 errors and 0 failures.
- A2: `pytest backend` still passes.
- A3: frontend jest passes; `ci_check.py` clean.

## Constraints
- Test-only change.
