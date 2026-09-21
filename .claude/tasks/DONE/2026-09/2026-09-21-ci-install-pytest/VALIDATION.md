# VALIDATION — 2026-09-21-ci-install-pytest

## v1
result: PASS
- A1: new step installs pytest into backend/.venv and mcp/.venv before both pytest steps; workflow YAML parses. PASS
- A2: diff touches only .github/workflows/harness-gate.yml (plus harness task files); Makefile unchanged. PASS
- Constraint: pins match dev extras. PASS
issues: []
