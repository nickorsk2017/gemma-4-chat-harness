"""image_analyzer MCP server entry point."""

from __future__ import annotations

from fastmcp import FastMCP

from image_analyzer.config import settings
from image_analyzer.tools import analyze_image

mcp = FastMCP("image_analyzer")
analyze_image.register(mcp)


def main() -> None:
    mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
