"""Load the sub-agents' MCP tools as LangChain tools, ready to bind to the model.

Discovery is dynamic and config-driven (mcp/CLAUDE.md): each configured sub-agent
is queried for its tools live, so the bound tool set stays correct as sub-agents
change. Tools coming from a file-consuming sub-agent (doc/image) are flagged so
the loop can inject the raw attached file at dispatch (R3) — the model never
carries the file bytes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from master_orchestrator.config import settings


@dataclass
class SubagentToolset:
    """The sub-agents' tools, ready to bind, plus the file-injection flag set."""

    tools: list[BaseTool]
    by_name: dict[str, BaseTool]
    file_tool_names: set[str]  # tools needing the attached file injected

    @classmethod
    async def load(cls) -> "SubagentToolset":
        """Fetch every configured sub-agent's tools via MCP and merge them."""
        client = MultiServerMCPClient(cls._server_specs())

        tools: list[BaseTool] = []
        file_tool_names: set[str] = set()
        for name in settings.subagents:
            agent_tools = await client.get_tools(server_name=name)
            tools.extend(agent_tools)
            if name in settings.file_subagents:
                file_tool_names.update(t.name for t in agent_tools)

        return cls(
            tools=tools,
            by_name={t.name: t for t in tools},
            file_tool_names=file_tool_names,
        )

    @staticmethod
    def _server_specs() -> dict[str, dict[str, object]]:
        """Sub-agent connection specs with the parent env forwarded.

        stdio sub-agents run as subprocesses; the MCP stdio client forwards only
        a safe subset of the environment when no ``env`` is given, dropping
        secrets like ``TAVILY_API_KEY``/``GEMMA_API_KEY``. Inject the full
        ``os.environ`` into each stdio spec so the container's env reaches every
        sub-agent (a spec-provided ``env`` still wins). http/sse specs — no
        subprocess — are passed through unchanged. The shared
        ``settings.subagents`` is copied, never mutated.
        """
        specs: dict[str, dict[str, object]] = {}
        for name, spec in settings.subagents.items():
            cfg = dict(spec)
            if cfg.get("transport", "stdio") == "stdio":
                cfg["env"] = {**os.environ, **(cfg.get("env") or {})}
            specs[name] = cfg
        return specs
