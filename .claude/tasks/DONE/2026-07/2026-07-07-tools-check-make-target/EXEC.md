# EXEC — 2026-07-07-tools-check-make-target

## v1
Makefile: added `tools-check` to `.PHONY` and a target after `news-check` that
runs `$(COMPOSE) exec mcp python scripts/tools_check.py $(ARGS)` with a `## `
help line. Runs inside the mcp container (WORKDIR /app, scripts at
/app/scripts) where the fleet is installed and sub-agents can spawn — unlike
news-check/gemma-check which only need host-side deps.
