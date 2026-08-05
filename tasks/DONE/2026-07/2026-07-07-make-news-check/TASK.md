# TASK — 2026-07-07-make-news-check
owner: Engineer
immutable: true

## Requirements
- R1: Makefile target `news-check` running mcp/scripts/news_check.py.
- R2: Runs inside the mcp container (deps live there): `docker compose exec mcp
  python scripts/news_check.py`, ARGS passthrough for --via/--query/--limit.
- R3: README make-target list stays in sync.

## Acceptance
- A1: `make news-check` / `make news-check ARGS="--via orchestrator"` invoke the
  script; target in .PHONY; help line present.
- A2: README lists the new target.
