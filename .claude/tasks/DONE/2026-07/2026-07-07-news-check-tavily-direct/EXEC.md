# EXEC — 2026-07-07-news-check-tavily-direct

## v1
news_check.py rewritten: stdlib MCP client straight to Tavily's hosted server —
key from env/.env, initialize -> initialized -> tools/call tavily_search
{query: "What is the last news?", topic: news, max_results: 5}; prints numbered
titles+urls from structuredContent (text fallback); URLError/no-key/empty ->
stderr + exit 1. Makefile + README help lines updated. 3 files.
