# EXEC — orchestrator-psycopg-libpq

## v1
- master_orchestrator/pyproject.toml: added `psycopg[binary]>=3.1` to
  `[project].dependencies` (between langgraph-checkpoint-postgres and pydantic),
  with a comment explaining the libpq bundling rationale.
- No code, Dockerfile, or sub-agent changes. TOML re-parsed: valid; psycopg[binary]
  present in dependencies.
