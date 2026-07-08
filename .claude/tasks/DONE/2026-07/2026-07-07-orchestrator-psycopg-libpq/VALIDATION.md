# VALIDATION — orchestrator-psycopg-libpq

## v1 — exec_version=1 — PASS
- A1: PASS — `psycopg[binary]>=3.1` declared; binary wheel bundles libpq, so
  AsyncPostgresSaver's psycopg connection finds a pq wrapper on python:3.11-slim.
- A2: PASS — pyproject.toml parses; dependencies list well-formed; only
  master_orchestrator touched.
- A3: PASS — no contract/code changes.
Note (ops): requires `docker compose up -d --build mcp` to reinstall deps into
the image. Result: PASS -> DONE.
