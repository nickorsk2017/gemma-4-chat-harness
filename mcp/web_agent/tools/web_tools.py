"""MCP tools for web_agent. Thin: validate -> provider -> envelope."""

from __future__ import annotations

from typing import Annotated

from langsmith import traceable

from fastmcp import FastMCP
from pydantic import Field

from agent_core.envelope import AgentResponse
from web_agent.providers import tavily
from web_agent.schemas.web import SearchResult

AGENT = "web_agent"

@traceable("web_agent.tools.providers.register")
def register(mcp: FastMCP) -> None:
    @traceable("run search web tool")
    @mcp.tool
    async def search_web(
        prompt: Annotated[str, Field(description="What to search the live web for.")],
        max_results: Annotated[
            int, Field(ge=1, le=10, description="How many results to return (1-10).")
        ] = 5,
    ) -> AgentResponse[SearchResult]:
        """Live internet search (Tavily): news, current events, fresh facts."""
        try:
            result = await tavily.search_web(prompt, max_results)
            return AgentResponse.ok(AGENT, result)
        except Exception as exc:
            return AgentResponse.fail(AGENT, str(exc))
