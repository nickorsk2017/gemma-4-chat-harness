"""doc_analyzer settings."""

from __future__ import annotations

from agent_core.llm import DEFAULT_MODEL, NOVITA_BASE_URL
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DocAnalyzerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DOC_ANALYZER_", env_file=".env", extra="ignore")

    host: str = "127.0.0.1"
    port: int = 8102
    transport: str = "stdio"  # "stdio" | "sse" | "streamable-http"

    # Always real: doc_analyzer decodes the PDF (pypdf) and calls gemma via
    # Novita's OpenAI-compatible endpoint. GEMMA_API_KEY (env) is REQUIRED;
    # there is no mock LLM fallback.
    llm_provider: str = "novita"
    llm_model: str = DEFAULT_MODEL
    llm_base_url: str = NOVITA_BASE_URL
    llm_api_key: str | None = Field(default=None, validation_alias="GEMMA_API_KEY")
    request_timeout_s: float = 30.0


settings = DocAnalyzerSettings()
