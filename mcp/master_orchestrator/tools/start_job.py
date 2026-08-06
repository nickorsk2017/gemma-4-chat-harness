"""MCP tool: ``start_job`` — route the prompt through the sub-agents.

Thin: validate -> Orchestrator service -> envelope. Stays inside the shared
fail-soft envelope (agent_core), never raising across the MCP boundary.
"""

from __future__ import annotations

from fastmcp import FastMCP

from agent_core.envelope import AgentResponse
from agent_core.ratelimit import RateLimited
from master_orchestrator.schemas.http import OrchestrateRequest, OrchestrationResult
from master_orchestrator.services.orchestrator import (
    RATE_LIMITED_CODE,
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
        except RateLimited as exc:
            # Carried as a code + retry_after_s, not a message: the gateway maps this
            # straight to a 429 with a Retry-After header (PLAN D4/D5).
            return AgentResponse.fail(
                AGENT, str(exc), code=RATE_LIMITED_CODE, retry_after_s=exc.retry_after_s
            )
        except TurnTimeout as exc:
            # Carried as a code, not a message: the client branches on it to offer a
            # retry, and message text is not a contract.
            return AgentResponse.fail(AGENT, str(exc), code=TURN_TIMEOUT_CODE)
        except Exception as exc:  # noqa: BLE001 - fail soft across the boundary
            return AgentResponse.fail(AGENT, str(exc))
