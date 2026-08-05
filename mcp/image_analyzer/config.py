"""image_analyzer settings."""

from __future__ import annotations

from agent_core.llm import DEFAULT_MODEL, NOVITA_BASE_URL
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ImageAnalyzerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="IMAGE_ANALYZER_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8103
    transport: str = "stdio"  # "stdio" | "sse" | "streamable-http"

    # LLM/vision: gemma via Novita's OpenAI-compatible endpoint. GEMMA_API_KEY
    # (env) is REQUIRED; there is no mock LLM fallback.
    llm_provider: str = "novita"
    llm_model: str = DEFAULT_MODEL
    llm_base_url: str = NOVITA_BASE_URL
    llm_api_key: str | None = Field(default=None, validation_alias="GEMMA_API_KEY")
    request_timeout_s: float = 30.0

    # --- guardrails gate (PLAN D7) ---------------------------------------------------
    # Declared here so a misconfigured gate fails at startup rather than at the first
    # request. agent_core.guardrails reads the same env vars at call time — these fields
    # declare the env contract, they are never passed into the call (one policy owner).
    guardrails_url: str = Field(
        default="http://guardrails:8200", validation_alias="GUARDRAILS_URL"
    )
    guardrails_timeout_s: float = Field(
        default=15.0, validation_alias="GUARDRAILS_TIMEOUT_S"
    )


settings = ImageAnalyzerSettings()
