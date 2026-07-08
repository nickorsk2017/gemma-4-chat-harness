"""web_agent MCP server entry point."""

from __future__ import annotations

from fastmcp import FastMCP

from web_agent.config import settings
from web_agent.tools import search_web

mcp = FastMCP("web_agent")
search_web.register(mcp)


def main() -> None:
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
