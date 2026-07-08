# EXEC — 2026-07-07-news-check-aiohttp

## v1
news_check.py implemented per PLAN v1: aiohttp async POST to
https://api.tavily.com/search, Bearer auth, body
{query,"search_depth":"advanced","topic":"news","max_results":5};
key from env/.env (parents[2]/.env), no hardcode; numbered title+url output;
exit 1 on no-key/ClientError/empty, else 0. Makefile news-check help line
updated to "direct aiohttp REST call to Tavily". 2 files.
