# TASK — 2026-07-05-env-orchestrator-db-url
owner: Engineer
immutable: true

## Requirements
- R1: .env (local, gitignored) contains ORCHESTRATOR_DATABASE_URL=postgresql://postgres:250244@postgres:5432/gemma-chat (no spaces around '=').
- R2: POSTGRES_USER/PASSWORD/DB in .env match the URL so the compose-provisioned postgres container and the derived mcp URL are consistent.

## Acceptance
- A1: .env parses (KEY=VALUE), creds consistent across POSTGRES_* and the URL.
