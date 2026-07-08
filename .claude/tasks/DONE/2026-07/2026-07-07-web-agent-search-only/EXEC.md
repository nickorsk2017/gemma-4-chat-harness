# EXEC — 2026-07-07-web-agent-search-only

## v1
Deleted providers/llm.py. web_tools.py reduced to the single search_web tool
with trimmed imports (tavily + SearchRequest/SearchResult only). tavily.py:
removed fetch_news and its unused imports. config.py comment corrected.
3 files edited, 1 deleted.
