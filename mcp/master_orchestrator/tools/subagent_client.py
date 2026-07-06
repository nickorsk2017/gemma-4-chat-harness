"""Sub-agent calls as LangChain tool calls via ``langchain-mcp-adapters``.

A single lazily-built ``MultiServerMCPClient`` maps every configured
``SubAgentEndpoint`` to a stdio/HTTP connection. Each dispatch resolves the
sub-agent's tool, invokes it under our own timeout (the adapters expose no
per-call timeout), and validates the output into a typed ``AgentResponse`` at
this boundary (rule 7 / R8): failures never raise, they come back as an error
envelope so one bad sub-agent can't sink the whole run (rule 6).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from agent_core.envelope import AgentResponse, Status
from master_orchestrator.config import settings

logger = logging.getLogger("master_orchestrator.subagents")

_client: MultiServerMCPClient | None = None


def _get_client() -> MultiServerMCPClient:
    """Build (once) the multi-server client from the sub-agent registry."""
    global _client
    if _client is None:
        _client = MultiServerMCPClient(
            {name: ep.to_connection() for name, ep in settings.subagents.items()},
            # Failures must surface as exceptions we convert to error envelopes,
            # not as success-shaped strings.
            handle_tool_errors=False,
        )
    return _client


async def _resolve_tool(agent: str, tool: str) -> BaseTool | None:
    """Look up ``tool`` on ``agent``'s server; ``None`` if it doesn't exist."""
    tools = await _get_client().get_tools(server_name=agent)
    for candidate in tools:
        if candidate.name == tool:
            return candidate
    return None


def _to_envelope(raw: Any, agent: str) -> AgentResponse[Any]:
    """Validate adapter tool output (dict or JSON text) into ``AgentResponse``."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return AgentResponse.fail(agent, f"unparseable sub-agent response: {raw!r}")
    # Adapters may return (content, artifact) tuples for content_and_artifact tools.
    if isinstance(raw, tuple) and raw:
        raw = raw[0]
    try:
        return AgentResponse.model_validate(raw)
    except Exception:  # noqa: BLE001 — malformed envelope is a sub-agent fault
        return AgentResponse.fail(agent, f"sub-agent returned a non-envelope: {raw!r}")


def _shape_args(schema: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    """Fit planner arguments to the tool schema — idempotently.

    Sub-agent tools take a single ``request`` model param, and the planner LLM
    is prompted to emit arguments already shaped ``{"request": {...}}``. Never
    wrap twice; unwrap when the adapter flattened the schema instead.
    """
    wrapped = set(arguments.keys()) == {"request"} and isinstance(
        arguments["request"], dict
    )
    if "request" in schema:
        return arguments if wrapped else {"request": arguments}
    return arguments["request"] if wrapped else arguments


async def call_subagent(
    agent: str, tool: str, arguments: dict[str, Any]
) -> AgentResponse[Any]:
    """Invoke ``tool`` on ``agent`` and return its typed envelope.

    Never raises across the boundary — timeouts, unknown agents/tools, and
    transport errors all come back as error envelopes. Every call is logged
    with its duration and outcome.
    """
    started = time.monotonic()
    envelope = await _call_subagent(agent, tool, arguments)
    elapsed = time.monotonic() - started
    if envelope.status is Status.OK:
        logger.info("subagent %s.%s ok in %.1fs", agent, tool, elapsed)
    else:
        logger.warning(
            "subagent %s.%s FAILED in %.1fs: %s", agent, tool, elapsed, envelope.error
        )
    return envelope


async def _call_subagent(
    agent: str, tool: str, arguments: dict[str, Any]
) -> AgentResponse[Any]:
    if agent not in settings.subagents:
        return AgentResponse.fail(agent, f"unknown agent {agent!r}")

    try:
        async with asyncio.timeout(settings.subagent_timeout_s):
            lc_tool = await _resolve_tool(agent, tool)
            if lc_tool is None:
                return AgentResponse.fail(
                    agent, f"unknown tool {tool!r} on agent {agent!r}"
                )
            raw = await lc_tool.ainvoke(_shape_args(lc_tool.args or {}, arguments))
        return _to_envelope(raw, agent)
    except TimeoutError:
        return AgentResponse.fail(agent, "sub-agent timed out")
    except Exception as exc:  # noqa: BLE001 — rule 7: fail soft, never raise
        return AgentResponse.fail(agent, str(exc))
