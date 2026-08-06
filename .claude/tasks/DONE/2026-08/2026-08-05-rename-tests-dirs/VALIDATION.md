# VALIDATION — 2026-08-05-rename-tests-dirs

## v1 (validation_version=1)
result: PASS

Checks:
- A1: backend/tests, mcp/tests, mcp/guardrails/tests confirmed absent; __tests__
  equivalents confirmed present (3/8/10 files respectively, content unchanged).
- A2: pytest collection reaches modules under __tests__ dirs (import errors seen
  are missing third-party deps in the exec sandbox, not a discovery/path issue).
- A3: grep of backend/pyproject.toml, mcp/pyproject.toml, Makefile, .github/workflows
  found no hardcoded "tests" path references to fix.

open_issues: []
