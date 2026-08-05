"""guardrails MCP server entry point.

Exposes ``check_input`` / ``check_output``. Unlike the other sub-agents it is reached by
*any* agent rather than only by the orchestrator (see the cross-cutting exemption in
mcp/CLAUDE.md), which is why it serves over HTTP rather than being spawned over stdio.
"""

from __future__ import annotations

import logging

from fastmcp import FastMCP

from guardrails.config import settings
from guardrails.detectors.pii import warmup as warm_pii
from guardrails.tools import check as check_tools

mcp = FastMCP("guardrails")
check_tools.register(mcp)


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    # Built before the server accepts a call, not on the first one: the analyzer's
    # first construction is seconds long. See guardrails.detectors.pii.warmup.
    warm_pii()
    if settings.transport in ("http", "streamable-http"):
        from agent_core.http_server import HttpServer

        HttpServer(
            mcp,
            name="guardrails",
            host=settings.http_host,
            port=settings.http_port,
            allowed_hosts=settings.http_allowed_hosts,
        ).run()
    else:
        mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
