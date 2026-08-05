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

# Sub-agents whose results carry text from outside the perimeter. Their output is gated
# on the way back into the model's context (PLAN D5). `doc_analyzer` is deliberately NOT
# here: its document is already checked on the way in, and its return is our own model's
# answer about already-checked input, so re-gating it buys a second model call for
# nothing (TASK A6-2).
UNTRUSTED_SUBAGENTS = ["web_agent"]


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
    untrusted_subagents: list[str] = Field(
        default_factory=lambda: list(UNTRUSTED_SUBAGENTS)
    )

    @property
    def file_subagents(self) -> set[str]:
        """Sub-agents whose tools receive the injected file at dispatch."""
        return {self.doc_subagent, self.image_subagent}

    # Tool-calling loop bound: how many model<->tool rounds before we stop. Fewer rounds
    # is what makes a turn fit the ceiling at all — every round can add a model call and
    # a sub-agent dispatch.
    max_tool_iterations: int = 2

    # The orchestrator's own budget for one turn, below the gateway's ceiling (66s) on
    # purpose. An outer timeout can only ever produce a transport error: by the time it
    # fires there is no agent response left to shape. This one fires first, while a live
    # code path still exists, so the turn can answer with a typed `turn_timeout` that the
    # UI renders as a retry the user can press.
    turn_budget_s: float = 60.0

    # Attachment cap (validated agent-side; the gateway forwards raw bytes).
    max_file_bytes: int = 15 * 1024 * 1024  # 15 MiB

    # Conversation memory cap (message history only; files are not persisted).
    history_max_messages: int = 20

    # Thread memory backend (LangGraph Postgres checkpointer). REQUIRED: thread
    # data is read from Postgres only — there is no in-memory fallback. A missing
    # value raises MemoryConfigError when the store is first built.
    # Env: ORCHESTRATOR_DATABASE_URL (psycopg conn string, e.g. postgresql://...).
    database_url: str | None = None



    # --- guardrails gate (TASK R10) -------------------------------------------------
    # Declared here so a misconfigured gate fails at startup rather than at the first
    # request. agent_core.guardrails reads the same env vars.
    guardrails_url: str = Field(
        default="http://guardrails:8200", validation_alias="GUARDRAILS_URL"
    )
    guardrails_timeout_s: float = Field(
        default=15.0, validation_alias="GUARDRAILS_TIMEOUT_S"
    )

settings = OrchestratorSettings()
