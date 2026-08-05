# VALIDATION — 2026-07-07-make-news-check

## v1 — PASS
- A1 PASS: `make -n news-check ARGS="--via orchestrator"` expands to
  `docker compose exec mcp python scripts/news_check.py --via orchestrator`;
  .PHONY updated; ## help line renders in `make help`.
- A2 PASS: README make-target block lists news-check.
- Live run needs the stack up — left to Engineer.
