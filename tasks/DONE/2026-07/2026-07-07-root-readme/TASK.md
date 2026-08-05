# TASK — 2026-07-07-root-readme
owner: Engineer
immutable: true

## Requirements
- R1: Create root `README.md`: what the project is, architecture & repo structure,
  the .claude execution harness (roles, task flow, runner), how to run (make /
  docker compose), env configuration, healthcheck.
- R2: Reflect the CURRENT state: LLM = google/gemma-4-31b-it via Novita
  (GEMMA_API_KEY), live web search via Tavily MCP (TAVILY_API_KEY), Postgres
  thread memory, LangSmith optional.
- R3: Concise, command-first, no duplication of subsystem CLAUDE.md content —
  link to them.

## Acceptance
- A1: README.md exists at repo root, covers overview/structure/harness/run/env.
- A2: All commands and ports match Makefile/docker-compose.yml.
