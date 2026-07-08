# TASK — orchestrator-psycopg-libpq
owner: Engineer
immutable: true

## Requirements
- R1: The orchestrator's LangGraph AsyncPostgresSaver checkpointer MUST connect
  to Postgres inside the mcp image (python:3.11-slim). Today memory boot fails
  with "no pq wrapper available ... libpq library not found" because psycopg has
  no libpq available.

## Acceptance
- A1: master_orchestrator declares a psycopg distribution that provides libpq on
  slim without an OS package.
- A2: pyproject.toml stays valid; no other subsystem touched.
- A3: gateway/orchestrator contracts unchanged.
