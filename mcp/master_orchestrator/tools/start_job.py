"""MCP tool: ``start_job`` — route the prompt through the sub-agents.

Thin: validate -> Orchestrator service -> envelope. Stays inside the shared
fail-soft envelope (agent_core), never raising across the MCP boundary.
"""

from __future__ import annotations

from fastmcp import FastMCP

from agent_core.envelope import AgentResponse
from master_orchestrator.schemas.http import OrchestrateRequest, OrchestrationResult
from master_orchestrator.services.orchestrator import (
    TURN_TIMEOUT_CODE,
    Orchestrator,
    TurnTimeout,
)

AGENT = "master_orchestrator"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def start_job(request: OrchestrateRequest) -> AgentResponse[OrchestrationResult]:
        """Route the prompt through the sub-agents and return one merged answer."""
        try:
            result = await Orchestrator().run(request)
            return AgentResponse.ok(AGENT, result)
        except TurnTimeout as exc:
            # Carried as a code, not a message: the client branches on it to offer a
            # retry, and message text is not a contract.
            return AgentResponse.fail(AGENT, str(exc), code=TURN_TIMEOUT_CODE)
        except Exception as exc:  # noqa: BLE001 - fail soft across the boundary
            return AgentResponse.fail(AGENT, str(exc))
