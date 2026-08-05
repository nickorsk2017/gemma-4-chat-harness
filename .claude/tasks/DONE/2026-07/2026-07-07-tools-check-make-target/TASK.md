# TASK — 2026-07-07-tools-check-make-target
owner: Engineer
immutable: true

## Requirements
- R1: Add a root `Makefile` target `tools-check` that runs
  `mcp/scripts/tools_check.py`. Because the script needs the full agent fleet
  installed and spawns sub-agents over MCP stdio, it must run INSIDE the mcp
  container: `docker compose exec mcp python scripts/tools_check.py`.
- R2: Follow existing conventions — `## ` help comment, add to `.PHONY`, support
  `ARGS=` passthrough like gemma-check/news-check.

## Acceptance
- A1: `make help` lists `tools-check`; `make tools-check` expands to the compose
  exec command with ARGS passthrough.

## Constraints
- Single file touched (Makefile); no new dependencies.
