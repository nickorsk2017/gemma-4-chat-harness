"""guardrails settings — every threshold, timeout and toggle is env-backed (TASK R10).

No policy constant is hardcoded below: the defaults here are the configuration's
default *values*, overridable per environment via ``GUARDRAILS_*``.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class GuardrailsSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="GUARDRAILS_", env_file=".env", extra="ignore"
    )

    # --- transport (this agent is reached over HTTP, not spawned over stdio) ---------
    transport: str = "streamable-http"
    http_host: str = "0.0.0.0"
    http_port: int = 8200
    # Docker service identities admitted past fastmcp's Host guard, so in-network
    # calls (Host: guardrails:8200) do not 421.
    http_allowed_hosts: list[str] = Field(
        default_factory=lambda: ["guardrails:8200", "localhost:8200", "127.0.0.1:8200"]
    )

    # --- category toggles (TASK R3) -------------------------------------------------
    check_sexual: bool = True
    check_drugs: bool = True
    check_injection: bool = True

    # --- thresholds ------------------------------------------------------------------
    # Model confidence at or above which a category is taken as present. There is no
    # lexicon threshold any more: keywords supply evidence, they decide nothing (D12).
    judge_threshold: float = 0.6

    # --- judge (PLAN R-1: its own budget, NOT the 90s agent_core default) -----------
    judge_enabled: bool = True
    judge_timeout_s: float = 8.0
    judge_model: str | None = None  # None -> GEMMA_MODEL / agent default
    judge_api_key: str | None = Field(default=None, validation_alias="GEMMA_API_KEY")
    judge_base_url: str = "https://api.novita.ai/openai"
    # PLAN R-2: cap what the judge sees for large documents. 0 disables the cap.
    judge_max_chars: int = 6000
    # The model runs on every checked text (TASK A3-2). There is no deterministic
    # short-circuit left to skip it with, which is the accepted cost of having it, and
    # not a switch: `judge_on_clean` is gone.

    # --- PII (TASK R4) ---------------------------------------------------------------
    pii_enabled: bool = True
    pii_score_threshold: float = 0.5
    # Unstructured personal data (names, addresses) is the model's job — there is no
    # NLP engine here to switch on any more (TASK A9-1).
    pii_model_entities: bool = True

    # --- medical path (TASK A3-5) ----------------------------------------------------
    # The human in the loop is the doctor reading the answer. A clinical question is
    # answered and carries a disclaimer; there is no held turn and no moderator queue.
    medical_disclaimer: bool = True

    # --- observability (TASK R11) ----------------------------------------------------
    log_decisions: bool = True


settings = GuardrailsSettings()
