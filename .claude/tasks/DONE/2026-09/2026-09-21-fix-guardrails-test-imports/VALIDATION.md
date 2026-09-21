# VALIDATION — 2026-09-21-fix-guardrails-test-imports

## v1
- A1: `pytest mcp` from repo root, non-editable install as in Makefile, Python 3.14 -> 248 passed, 4 skipped in 2.10s. PASS
- A2: `pytest backend` -> 10 passed, 3 warnings in 0.80s. PASS
- A3: frontend `pnpm test` with frozen lockfile -> Tests:       34 passed, 34 total. PASS
- Constraint: only test files changed. PASS
- result: PASS
