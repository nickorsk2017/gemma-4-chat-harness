"""MCP tools for guardrails. Thin: set direction -> pipeline -> envelope.

No policy lives here — the cascade owns all of it (mcp/CLAUDE.md rule 3). The two tools
are the whole surface of this agent; nothing else is exposed.
"""

from __future__ import annotations

from fastmcp import FastMCP

from agent_core.envelope import AgentResponse
from guardrails.schemas.verdict import CheckRequest, Direction, Verdict
from guardrails.services.pipeline import check

AGENT = "guardrails"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def check_input(request: CheckRequest) -> AgentResponse[Verdict]:
        """Gate a prompt, a document or a tool result before it reaches the LLM."""
        try:
            request.direction = Direction.INPUT
            return AgentResponse.ok(AGENT, await check(request))
        except Exception as exc:  # noqa: BLE001 - never raise across the MCP boundary
            return AgentResponse.fail(AGENT, str(exc))

    @mcp.tool
    async def check_output(request: CheckRequest) -> AgentResponse[Verdict]:
        """Gate an answer before it is returned to the user."""
        try:
            request.direction = Direction.OUTPUT
            return AgentResponse.ok(AGENT, await check(request))
        except Exception as exc:  # noqa: BLE001 - never raise across the MCP boundary
            return AgentResponse.fail(AGENT, str(exc))
