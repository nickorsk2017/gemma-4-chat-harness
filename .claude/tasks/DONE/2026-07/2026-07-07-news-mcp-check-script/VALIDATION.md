# VALIDATION — 2026-07-07-news-mcp-check-script

## v1 — PASS
- A1 PASS: stub fastmcp run, 4 scenarios — agent ok (items printed, exit 0),
  agent error envelope (stderr, exit 1), orchestrator ok with web_agent routing
  (exit 0), orchestrator misroute (warning, exit 1).
- A2 PASS: covered by the two failing scenarios above.
- Live runs left to Engineer (need running stack / local deps):
  `docker compose exec mcp python scripts/news_check.py` and
  `python3 mcp/scripts/news_check.py --via orchestrator`.
