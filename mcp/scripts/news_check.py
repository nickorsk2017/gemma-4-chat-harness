#!/usr/bin/env python3
"""news_check.py — direct liveness check against Tavily's REST search API.

No agents, no orchestrator, no LLM: a single ``aiohttp`` POST to
``https://api.tavily.com/search`` with the API key as a Bearer token, then the
results are printed. ``TAVILY_API_KEY`` is read from the environment or the
repo-root ``.env``. Exit 0 when results come back, 1 on any error.
"""

from __future__ import annotations

import asyncio
import os
import ssl
import sys
from pathlib import Path

import aiohttp

try:
    import certifi

    _CAFILE = certifi.where()
except ImportError:  # certifi absent -> fall back to the system trust store
    _CAFILE = None

TAVILY_URL = "https://api.tavily.com/search"
QUERY = "What is the last news?"


def _load_api_key() -> str | None:
    """TAVILY_API_KEY from the environment, falling back to repo-root .env."""
    key = os.environ.get("TAVILY_API_KEY")
    if key:
        return key.strip()
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line.startswith("TAVILY_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip("'\"") or None
    return None


async def _search(api_key: str) -> list[dict]:
    """POST the query to Tavily and return its ``results`` list."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "query": QUERY,
        "search_depth": "advanced",
        "topic": "news",
        "max_results": 5,
    }
    timeout = aiohttp.ClientTimeout(total=30)
    ssl_ctx = ssl.create_default_context(cafile=_CAFILE)
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        async with session.post(TAVILY_URL, json=payload, headers=headers) as resp:
            resp.raise_for_status()
            data = await resp.json()
    results = data.get("results", [])
    return results if isinstance(results, list) else []


async def _main() -> int:
    api_key = _load_api_key()
    if not api_key:
        print("error: TAVILY_API_KEY is not set (env or repo-root .env)", file=sys.stderr)
        return 1
    try:
        results = await _search(api_key)
    except aiohttp.ClientError as exc:
        print(f"error: Tavily request failed: {exc}", file=sys.stderr)
        return 1
    if not results:
        print("error: Tavily returned no results", file=sys.stderr)
        return 1
    print(f'Tavily news results for: "{QUERY}"\n')
    for i, item in enumerate(results, 1):
        title = str(item.get("title", "")).strip() or "(untitled)"
        url = str(item.get("url", "")).strip()
        print(f"{i}. {title}\n   {url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
