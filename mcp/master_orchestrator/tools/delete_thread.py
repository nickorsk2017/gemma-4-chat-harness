"""MCP tool: ``delete_thread`` — forget a conversation thread.

Thin: get_store -> delete -> envelope. Stays inside the shared fail-soft envelope
(agent_core), never raising across the MCP boundary.
"""

from __future__ import annotations

from fastmcp import FastMCP

from agent_core.envelope import AgentResponse
from master_orchestrator.services.memory import get_store

AGENT = "master_orchestrator"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def delete_thread(thread_id: str) -> AgentResponse[dict]:
        """Forget a conversation thread (history + stored documents)."""
        try:
            store = await get_store()
            deleted = await store.delete(thread_id)
            return AgentResponse.ok(AGENT, {"thread_id": thread_id, "deleted": deleted})
        except Exception as exc:  # noqa: BLE001 - fail soft across the boundary
            return AgentResponse.fail(AGENT, str(exc))
