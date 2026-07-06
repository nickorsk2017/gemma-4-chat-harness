"""The orchestrator's own MCP tools: orchestrate a prompt, manage threads."""

from __future__ import annotations

from fastmcp import FastMCP

from master_orchestrator.db.checkpointer import get_checkpointer
from master_orchestrator.schemas.http import OrchestrateRequest
from master_orchestrator.schemas.plan import OrchestrationResult
from master_orchestrator.tools.graph import run_orchestration
from agent_core.envelope import AgentResponse

AGENT = "master_orchestrator"


def register(mcp: FastMCP) -> None:
    @mcp.tool
    async def orchestrate(request: OrchestrateRequest) -> AgentResponse[OrchestrationResult]:
        """Split the prompt into sub-tasks, run the relevant sub-agents in
        parallel, and return one merged answer."""
        try:
            result = await run_orchestration(request)
            return AgentResponse.ok(AGENT, result, subtasks=len(result.results))
        except Exception as exc:  # noqa: BLE001
            return AgentResponse.fail(AGENT, str(exc))

    @mcp.tool
    async def delete_thread(thread_id: str) -> AgentResponse[dict]:
        """Delete a conversation thread (messages + stored documents) from the
        LangGraph checkpointer. Idempotent: deleting an unknown thread is ok."""
        key = (thread_id or "").strip()
        if not key:
            return AgentResponse.fail(AGENT, "thread_id is required")
        try:
            saver = await get_checkpointer()
            # BaseCheckpointSaver.adelete_thread (langgraph>=1.0): implemented
            # by both InMemorySaver and AsyncPostgresSaver.
            await saver.adelete_thread(key)
            return AgentResponse.ok(AGENT, {"thread_id": key, "deleted": True})
        except Exception as exc:  # noqa: BLE001 - fail-soft envelope, never a crash
            return AgentResponse.fail(AGENT, str(exc))
