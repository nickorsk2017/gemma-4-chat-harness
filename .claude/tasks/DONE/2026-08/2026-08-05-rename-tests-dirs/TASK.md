# TASK — 2026-08-05-rename-tests-dirs
owner: Engineer
immutable: true

## Requirements
- R1: Rename directory `backend/tests` to `backend/__tests__`.
- R2: Rename directory `mcp/tests` to `mcp/__tests__`.
- R3: Rename directory `mcp/guardrails/tests` to `mcp/guardrails/__tests__`.
- R4: Update any config/tooling references to the old `tests` paths (e.g. pytest
  testpaths, CI workflows, Makefile targets, pyproject.toml) so test discovery
  still works after the rename.

## Acceptance
- A1: `backend/tests`, `mcp/tests`, `mcp/guardrails/tests` no longer exist; the
  renamed `__tests__` directories exist in their place with identical contents.
- A2: Test discovery still works (e.g. `pytest` runs successfully from `backend/`
  and `mcp/`) after the rename.
- A3: No leftover references to the old `tests` path strings in config/CI files.

## Constraints
- Use `git mv` (or equivalent) to preserve history where possible.
- Do not touch `frontend/__tests__` (already correctly named).
