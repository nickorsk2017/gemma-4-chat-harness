# EXEC — 2026-09-21-ci-install-pytest

## v1
- R2: added step "Install test deps" to `.github/workflows/harness-gate.yml` between "Install frontend deps" and "Run backend pytest"; installs pytest>=8.0.0 and pytest-asyncio>=0.23.0 into backend/.venv and mcp/.venv.
- changed files: .github/workflows/harness-gate.yml
