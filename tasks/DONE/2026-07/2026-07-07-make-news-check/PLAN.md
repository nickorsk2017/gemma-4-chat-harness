# PLAN — 2026-07-07-make-news-check

## v1
Mirror gemma-check ergonomics but run in-container (fastmcp/web_agent deps are
baked in the mcp image; TAVILY/GEMMA env already injected by compose):
- Makefile: add `news-check` to .PHONY; target `$(COMPOSE) exec mcp python
  scripts/news_check.py $(ARGS)` with `##` help text noting ARGS.
- README: add one line to the make-target block.
Both agent and orchestrator modes work in-container (server binds 0.0.0.0:8100).
