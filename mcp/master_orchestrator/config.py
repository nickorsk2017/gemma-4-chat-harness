"""master_orchestrator settings, including the sub-agent MCP client registry."""

from __future__ import annotations

import os
from typing import Any

from agent_core.llm import DEFAULT_NVIDIA_MODEL, NVIDIA_BASE_URL
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SubAgentEndpoint(BaseModel):
    """How to reach one sub-agent's MCP server.

    For local dev the orchestrator spawns each sub-agent over stdio using
    ``command`` + ``args``. For a networked deploy set ``url`` and the client
    connects over streamable HTTP instead.
    """

    name: str
    command: str = "python"
    args: list[str] = Field(default_factory=list)
    url: str | None = None

    def to_connection(self) -> dict[str, Any]:
        """Map this endpoint to a ``langchain-mcp-adapters`` Connection dict.

        stdio connections pass the parent environment through explicitly: the
        MCP stdio transport spawns subprocesses with a minimal default env, so
        without this GEMMA_API_KEY / LANGSMITH_* never reach the sub-agents.
        """
        if self.url:
            return {"url": self.url, "transport": "http"}
        return {
            "command": self.command,
            "args": self.args,
            "transport": "stdio",
            "env": dict(os.environ),
        }


class OrchestratorSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ORCHESTRATOR_", env_file=".env", extra="ignore"
    )

    transport: str = "stdio"

    # HTTP serving (used when transport is "http"/"streamable-http"; the
    # composed stack sets these via env — config, not constants).
    http_host: str = "0.0.0.0"
    http_port: int = 8100
    # Host header values fastmcp's request guard must accept in addition to
    # localhost defaults — the docker service identity the gateway dials.
    http_allowed_hosts: list[str] = Field(
        default_factory=lambda: ["mcp", "mcp:8100"]
    )

    # LLM used for task splitting + final synthesis — gemma via the NVIDIA
    # OpenAI-compatible endpoint. GEMMA_API_KEY (env) is REQUIRED; there is
    # no mock LLM fallback.
    llm_provider: str = "nvidia"
    llm_model: str = DEFAULT_NVIDIA_MODEL
    llm_base_url: str = NVIDIA_BASE_URL
    llm_api_key: str | None = Field(default=None, validation_alias="GEMMA_API_KEY")

    # Hard cap so one slow sub-agent can't hang the whole request (rule 6).
    # Sub-agents make real gemma calls over full documents/images — allow for it,
    # but stay below the gateway's total budget (GATEWAY_ORCHESTRATOR_TIMEOUT_S).
    subagent_timeout_s: float = 120.0

    # --- Thread memory (LangGraph checkpointer) ---
    # PostgreSQL DSN for AsyncPostgresSaver (ORCHESTRATOR_DATABASE_URL). When
    # unset, an in-process InMemorySaver is used: fine for a long-lived dev
    # server, but cross-request memory in the composed stack needs Postgres.
    database_url: str | None = None
    # Caps for what gets injected into prompts from the thread (config, not
    # constants): last N messages of history, max chars of stored doc text.
    history_max_messages: int = 10
    document_max_chars: int = 12000

    # LangSmith tracing — canonical LANGSMITH_* env names (not ORCHESTRATOR_-prefixed).
    langsmith_tracing: bool = Field(
        default=False, validation_alias="LANGSMITH_TRACING"
    )
    langsmith_api_key: str | None = Field(
        default=None, validation_alias="LANGSMITH_API_KEY"
    )
    langsmith_project: str = Field(
        default="agent-chat", validation_alias="LANGSMITH_PROJECT"
    )

    @property
    def subagents(self) -> dict[str, SubAgentEndpoint]:
        return {
            "web_agent": SubAgentEndpoint(
                name="web_agent", args=["-m", "web_agent.main"]
            ),
            "doc_analyzer": SubAgentEndpoint(
                name="doc_analyzer", args=["-m", "doc_analyzer.main"]
            ),
            "image_analyzer": SubAgentEndpoint(
                name="image_analyzer", args=["-m", "image_analyzer.main"]
            ),
        }


settings = OrchestratorSettings()
