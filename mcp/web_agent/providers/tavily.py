"""Tavily REST provider — live internet search & news via ``aiohttp``.

Direct POSTs to Tavily's REST search API (``tavily_api_url``); no hosted MCP
server. ``TAVILY_API_KEY`` is required — a missing key raises so the tool layer
reports it in the response envelope. Endpoint and timeout come from ``config``.
"""

from __future__ import annotations

import ssl

import aiohttp

from web_agent.config import settings
from web_agent.schemas.web import SearchItem, SearchResult

try:  # certifi CA bundle if available; else fall back to the system trust store
    import certifi

    _CAFILE = certifi.where()
except ImportError:
    _CAFILE = None


async def fetch_data(query: str, max_results: int, topic: str) -> list[dict]:
    """POST to Tavily's REST search endpoint and return its ``results`` list."""
    api_key = settings.tavily_api_key
    if not api_key:
        raise RuntimeError(
            "TAVILY_API_KEY is not set — live web search is unavailable."
        )
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "query": query,
        "search_depth": "advanced",
        "topic": topic,
        "max_results": max_results,
    }
    timeout = aiohttp.ClientTimeout(total=settings.tavily_timeout_s)
    ssl_ctx = ssl.create_default_context(cafile=_CAFILE)
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        async with session.post(
            settings.tavily_api_url, json=payload, headers=headers
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
    results = data.get("results", [])
    return results if isinstance(results, list) else []


async def search_web(query: str, max_results: int) -> SearchResult:
    raw = await fetch_data(query, max_results, topic="general")
    return SearchResult(
        query=query,
        results=[
            SearchItem(
                title=str(r.get("title", "")),
                url=str(r.get("url", "")),
                content=str(r.get("content", ""))[:1000],
            )
            for r in raw
        ],
    )
