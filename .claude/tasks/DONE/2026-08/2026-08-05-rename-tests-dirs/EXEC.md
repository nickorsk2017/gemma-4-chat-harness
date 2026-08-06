# EXEC — 2026-08-05-rename-tests-dirs

## v1 (exec_version=1)
Implements TASK.md R1-R4 directly (LOW complexity, no PLAN.md).

- Renamed via `git mv`:
  - `backend/tests` -> `backend/__tests__`
  - `mcp/tests` -> `mcp/__tests__`
  - `mcp/guardrails/tests` -> `mcp/guardrails/__tests__`
- R4: audited `backend/pyproject.toml`, `mcp/pyproject.toml`, `Makefile`,
  `.github/workflows/harness-gate.yml` for hardcoded `tests` path references.
  None found (pytest has no `testpaths` config; discovery is default/recursive).
  No config changes required.
- Verified test discovery: `pytest --collect-only` from `backend/` and `mcp/`
  finds modules under the renamed `__tests__` dirs (collection errors present
  are pre-existing missing-dependency issues in the exec sandbox — pydantic/
  fastapi not installed — unrelated to the rename).
- Removed stale `__pycache__` under the old-path test dirs where permitted
  (some `.pyc` files on the host mount could not be removed due to sandbox
  file permissions; they are gitignored/untracked and harmless).

### Changed files
- `backend/tests/**` -> `backend/__tests__/**` (rename, no content change)
- `mcp/tests/**` -> `mcp/__tests__/**` (rename, no content change)
- `mcp/guardrails/tests/**` -> `mcp/guardrails/__tests__/**` (rename, no content change)
