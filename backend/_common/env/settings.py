"""Environment-backed settings (pydantic-settings). Config, not constants.

All URLs, modes, timeouts and origins come from the environment (prefix
``GATEWAY_``) or a local ``.env`` file. No secrets are hardcoded.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

OrchestratorMode = Literal["http", "stdio"]


class Settings(BaseSettings):
    """Gateway settings. Loaded from env / ``.env`` with the ``GATEWAY_`` prefix."""

    model_config = SettingsConfigDict(
        env_prefix="GATEWAY_", env_file=".env", extra="ignore"
    )

    # --- HTTP server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- CORS (the frontend origin[s]) ---
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- Orchestrator MCP integration ---
    # The gateway is an MCP *client* of master_orchestrator. Mode selects transport:
    # "stdio" -> spawn the orchestrator MCP server as a subprocess (default).
    # "http"  -> connect to an already-running orchestrator MCP server over HTTP.
    orchestrator_mode: OrchestratorMode = "stdio"

    # Attachments now travel inline (base64) to the orchestrator; the gateway no
    # longer writes uploads to disk, so there is no upload_dir here.

    # stdio transport: how to spawn the orchestrator (config, not constants).
    orchestrator_command: str = "python"
    orchestrator_args: list[str] = Field(
        default_factory=lambda: ["-m", "master_orchestrator.main"]
    )

    # http transport: URL of the running orchestrator MCP server.
    orchestrator_mcp_url: str = "http://127.0.0.1:8100/mcp"

    # shared: tool name to invoke and the per-request hard timeout.
    # Must exceed the whole LLM chain: planner + slowest sub-agent (see
    # ORCHESTRATOR_SUBAGENT_TIMEOUT_S) + synthesis.
    orchestrator_tool: str = "start_job"
    # Tool that deletes a conversation thread from the orchestrator's memory.
    orchestrator_delete_tool: str = "delete_thread"
    orchestrator_timeout_s: float = 180.0
    # Thread deletion is a checkpointer call, not an LLM chain — keep it short.
    orchestrator_delete_timeout_s: float = 30.0

    # --- Persistence (scaffolded; not on the mock chat path) ---
    database_url: str = "sqlite+aiosqlite:///./gateway.db"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton (safe to use as a FastAPI dependency)."""
    return Settings()
