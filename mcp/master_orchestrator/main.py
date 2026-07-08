"""master_orchestrator MCP server entry point.

Exposes two tools the gateway depends on:
- ``start_job``      -> AgentResponse[OrchestrationResult] (the merged answer).
- ``delete_thread``  -> AgentResponse[dict] acknowledgement.
Both stay inside the shared fail-soft envelope (agent_core), never raising across
the MCP boundary. Business logic lives in ``services/``; the tools are thin.
"""

from __future__ import annotations

from fastmcp import FastMCP

from master_orchestrator.config import settings
from master_orchestrator.tools import delete_thread, start_job

mcp = FastMCP("master_orchestrator")
start_job.register(mcp)
delete_thread.register(mcp)


def main() -> None:
    if settings.transport in ("http", "streamable-http"):
        from master_orchestrator.services.http_server import HttpServer

        HttpServer(mcp, settings).run()
    else:
        mcp.run(transport=settings.transport)


if __name__ == "__main__":
    main()
