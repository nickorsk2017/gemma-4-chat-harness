"""Transport to the master_orchestrator agent — a thin MCP proxy.

The gateway is a PURE PROXY: it holds no orchestration logic. This module is the
one place that speaks MCP. It invokes the agent's ``start_job`` / ``delete_thread``
tools and passes the agent's response back through unchanged (wrapped only in the
transport-level ``AgentOutcome``). All decisions — routing, thread_id generation,
validation, memory — live in the agent.

One implementation, one Protocol. fastmcp's ``Client`` accepts either a stdio
spawn spec (``{command, args}``) or a URL, so a single class covers both transports;
the mode only selects which target to hand it. The client never raises across its
boundary: failures come back as ``AgentOutcome(ok=False)``.
"""

from __future__ import annotations

import asyncio
from typing import Any, Protocol

from pydantic import BaseModel, Field
from fastmcp import Client

from _common.env import Settings
from gateway.schemas.chat import FilePayload


class AgentOutcome(BaseModel):
    """Normalized transport result of one agent call.

    ``data`` is the agent's payload passed through verbatim (e.g. the
    OrchestrationResult dict: ``{prompt, answer, results, thread_id}``). The
    gateway does not interpret it.
    """

    ok: bool
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class AgentClient(Protocol):
    """Anything that can forward a prompt to the agent and manage its threads."""

    async def send(
        self,
        prompt: str,
        file: FilePayload | None = None,
        thread_id: str | None = None,
    ) -> AgentOutcome: ...

    async def delete_thread(self, thread_id: str) -> AgentOutcome: ...


def _extract(result: Any) -> Any:
    """Pull the structured envelope out of a FastMCP tool result."""
    data = getattr(result, "structured_content", None)
    if data is None:
        data = getattr(result, "data", None)
    if data is not None:
        return data
    content = getattr(result, "content", None)
    if content:
        return getattr(content[0], "text", None)
    return None


def _to_outcome(payload: Any, *, expect_data: bool) -> AgentOutcome:
    """Map the agent's AgentResponse envelope to a transport outcome.

    Envelope shape (agent_core.envelope.AgentResponse):
        {status: "ok"|"error", agent, data, error, meta}
    On success we pass ``data`` through unchanged; on error we surface ``error``.
    """
    if not isinstance(payload, dict):
        return AgentOutcome(ok=False, error="malformed agent payload")
    if payload.get("status") == "error":
        return AgentOutcome(ok=False, error=payload.get("error") or "agent error")
    data = payload.get("data")
    if expect_data and not isinstance(data, dict):
        return AgentOutcome(ok=False, error="empty agent payload")
    return AgentOutcome(ok=True, data=data if isinstance(data, dict) else {})


async def _call_tool(
    target: Any, tool: str, timeout: float, arguments: dict[str, Any]
) -> Any | AgentOutcome:
    try:
        async with asyncio.timeout(timeout):
            async with Client(target) as client:
                result = await client.call_tool(tool, arguments)
        return _extract(result)
    except TimeoutError:
        return AgentOutcome(ok=False, error="agent timed out")
    except Exception as exc:  # noqa: BLE001 - fail soft across the boundary
        return AgentOutcome(ok=False, error=str(exc))


class McpAgentClient:
    """The single MCP proxy client (stdio spawn or HTTP URL, chosen by config)."""

    def __init__(self, settings: Settings) -> None:
        if settings.orchestrator_mode == "http":
            self._target: Any = settings.orchestrator_mcp_url
        elif settings.orchestrator_mode == "stdio":
            self._target = {
                "command": settings.orchestrator_command,
                "args": settings.orchestrator_args,
            }
        else:
            raise ValueError(f"Unknown orchestrator mode: {settings.orchestrator_mode!r}")
        self._tool = settings.orchestrator_tool
        self._timeout = settings.orchestrator_timeout_s
        self._delete_tool = settings.orchestrator_delete_tool
        self._delete_timeout = settings.orchestrator_delete_timeout_s

    async def send(
        self,
        prompt: str,
        file: FilePayload | None = None,
        thread_id: str | None = None,
    ) -> AgentOutcome:
        request: dict[str, Any] = {"prompt": prompt}
        if file is not None:
            request["file"] = file.model_dump()
        if thread_id:
            request["thread_id"] = thread_id
        payload = await _call_tool(
            self._target, self._tool, self._timeout, {"request": request}
        )
        if isinstance(payload, AgentOutcome):  # transport failure
            return payload
        return _to_outcome(payload, expect_data=True)

    async def delete_thread(self, thread_id: str) -> AgentOutcome:
        payload = await _call_tool(
            self._target, self._delete_tool, self._delete_timeout,
            {"thread_id": thread_id},
        )
        if isinstance(payload, AgentOutcome):  # transport failure
            return payload
        return _to_outcome(payload, expect_data=False)


def build_agent_client(settings: Settings) -> AgentClient:
    """Factory: the single MCP proxy client (transport chosen from settings)."""
    return McpAgentClient(settings)
