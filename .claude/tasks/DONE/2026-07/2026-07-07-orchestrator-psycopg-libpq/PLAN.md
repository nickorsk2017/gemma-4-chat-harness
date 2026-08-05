# PLAN — orchestrator-psycopg-libpq

## v1
Root cause: `langgraph-checkpoint-postgres` depends on psycopg 3 but not its
binary build. On python:3.11-slim there is no system libpq, so psycopg's c /
binary / python impls all fail to find a pq wrapper at first checkpointer use.

Options considered:
1. Add OS libpq via `apt-get install -y libpq5` in the Dockerfile (+ psycopg pure).
   - Extra apt layer; must also ensure pure-python psycopg is pulled; heavier image.
2. Depend on `psycopg[binary]` — the binary wheel bundles libpq. No apt layer,
   self-contained, standard for langgraph+Postgres on slim. CHOSEN.

Decision: add `psycopg[binary]>=3.1` to master_orchestrator dependencies. Scope
stays the orchestrator distribution; Dockerfile unchanged (pip install picks up
the new dep). `psycopg-pool` already arrives transitively via
langgraph-checkpoint-postgres; only the pq wrapper was missing.

Risk: binary wheel availability for the target platform — psycopg-binary ships
manylinux/macOS wheels covering the slim (glibc) runtime; fine.
