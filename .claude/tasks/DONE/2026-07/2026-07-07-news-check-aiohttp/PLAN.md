# PLAN — 2026-07-07-news-check-aiohttp

## v1
Replace the empty news_check.py with an async aiohttp client hitting Tavily's
REST endpoint directly (POST https://api.tavily.com/search), superseding the
earlier hosted-MCP approach per Engineer directive.

Design:
- _load_api_key(): env TAVILY_API_KEY first, else parse repo-root .env
  (parents[2] of the script) for TAVILY_API_KEY=; strip quotes. No hardcoding.
- _search(key): aiohttp.ClientSession POST with headers
  {Content-Type, Authorization: Bearer <key>} and body
  {query:"What is the last news?", search_depth:"advanced", topic:"news",
  max_results:5}; raise_for_status; return data["results"].
- _main(): no key -> stderr+exit 1; ClientError -> stderr+exit 1; empty -> exit 1;
  else print numbered title+url, exit 0. Entry via asyncio.run.
- Makefile: update news-check help line (stdlib -> aiohttp REST). README already
  documents TAVILY_API_KEY; no change needed.

New dependency: aiohttp (script-level HTTP client) -> MEDIUM complexity.
