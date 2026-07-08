"""master_orchestrator settings. Config, not constants (mcp/CLAUDE.md rule 5).

The sub-agent set is discovered from this registry (env-overridable), never a
hardcoded tool list: tools are fetched live from each configured MCP server.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# How to reach each sub-agent MCP server (FastMCP stdio spawn spec). The key is
# the sub-agent name; `python -m <name>.main` launches its server.
DEFAULT_SUBAGENTS: dict[str, dict[str, object]] = {
    "web_agent": {"command": "python", "args": ["-m", "web_agent.main"], "transport": "stdio"},
    "doc_analyzer": {"command": "python", "args": ["-m", "doc_analyzer.main"], "transport": "stdio"},
    "image_analyzer": {"command": "python", "args": ["-m", "image_analyzer.main"], "transport": "stdio"},
}

# Sub-agents whose tools consume the attached FILE. Their tool calls get the raw
# base64 file injected at dispatch — the model never carries the file bytes.
DOC_SUBAGENT = "doc_analyzer"
IMAGE_SUBAGENT = "image_analyzer"


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ORCHESTRATOR_", env_file=".env", extra="ignore"
    )

    transport: str = "stdio"  # server transport for the orchestrator itself

    # HTTP serving (used when transport is "http"/"streamable-http"; the composed
    # stack sets ORCHESTRATOR_TRANSPORT=streamable-http and binds 0.0.0.0:8100 so
    # the gateway can reach it at http://mcp:8100/mcp). Env: ORCHESTRATOR_HTTP_HOST,
    # ORCHESTRATOR_HTTP_PORT, ORCHESTRATOR_HTTP_ALLOWED_HOSTS.
    http_host: str = "0.0.0.0"
    http_port: int = 8100
    # Docker service identities the gateway dials; admitted past fastmcp's Host
    # guard so in-network calls (Host: mcp:8100) don't 421.
    http_allowed_hosts: list[str] = Field(
        default_factory=lambda: ["mcp:8100", "localhost:8100", "127.0.0.1:8100"]
    )

    subagents: dict[str, dict[str, object]] = Field(default_factory=lambda: dict(DEFAULT_SUBAGENTS))
    doc_subagent: str = DOC_SUBAGENT
    image_subagent: str = IMAGE_SUBAGENT

    @property
    def file_subagents(self) -> set[str]:
        """Sub-agents whose tools receive the injected file at dispatch."""
        return {self.doc_subagent, self.image_subagent}

    # Tool-calling loop bound: how many model<->tool rounds before we stop.
    max_tool_iterations: int = 4

    # Attachment cap (validated agent-side; the gateway forwards raw bytes).
    max_file_bytes: int = 15 * 1024 * 1024  # 15 MiB

    # Conversation memory cap (message history only; files are not persisted).
    history_max_messages: int = 20

    # Thread memory backend (LangGraph Postgres checkpointer). REQUIRED: thread
    # data is read from Postgres only — there is no in-memory fallback. A missing
    # value raises MemoryConfigError when the store is first built.
    # Env: ORCHESTRATOR_DATABASE_URL (psycopg conn string, e.g. postgresql://...).
    database_url: str | None = None


settings = OrchestratorSettings()
