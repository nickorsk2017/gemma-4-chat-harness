"""LangChain chat-model factory shared by all agents.

Every agent talks to a real model — ``google/gemma-4-31b-it`` served by the
NVIDIA OpenAI-compatible endpoint by default. There is NO mock fallback: a
missing ``GEMMA_API_KEY`` raises ``LLMConfigError`` at model-build time.
"""

from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
DEFAULT_NVIDIA_MODEL = "google/gemma-4-31b-it"

# Per-request hard timeout for LLM HTTP calls. Without it the OpenAI SDK waits
# up to 600s and retries with backoff — a hanging endpoint then silently eats
# the whole sub-agent budget. Keep below ORCHESTRATOR_SUBAGENT_TIMEOUT_S.
DEFAULT_REQUEST_TIMEOUT_S = 90.0


def _request_timeout() -> float:
    return float(os.environ.get("LLM_REQUEST_TIMEOUT_S", DEFAULT_REQUEST_TIMEOUT_S))


class LLMConfigError(RuntimeError):
    """The LLM is misconfigured (missing key / removed provider)."""


def build_chat_model(
    *,
    provider: str = "nvidia",
    model: str = DEFAULT_NVIDIA_MODEL,
    api_key: str | None = None,
    base_url: str | None = None,
    temperature: float = 0.0,
) -> BaseChatModel:
    """Build a real LangChain chat model.

    ``provider`` and ``api_key`` come from an agent's ``config.py``.
    ``base_url`` targets any OpenAI-compatible endpoint (defaults to the
    NVIDIA endpoint for the ``"nvidia"`` provider).
    """
    if provider == "mock":
        raise LLMConfigError(
            "The mock LLM has been removed — set GEMMA_API_KEY and use a real "
            "provider (nvidia/openai/anthropic)."
        )
    if not api_key:
        raise LLMConfigError(
            "GEMMA_API_KEY is not set. All agents require a real key for "
            f"{DEFAULT_NVIDIA_MODEL} via {NVIDIA_BASE_URL}; there is no mock fallback."
        )

    if provider == "nvidia":  # OpenAI-compatible NVIDIA endpoint (gemma et al.)
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            base_url=base_url or NVIDIA_BASE_URL,
            timeout=_request_timeout(),
            max_retries=1,
        )

    if provider == "openai":  # pragma: no cover - requires extra + key
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model,
            api_key=api_key,
            temperature=temperature,
            base_url=base_url,
            timeout=_request_timeout(),
            max_retries=1,
        )

    if provider == "anthropic":  # pragma: no cover - requires extra + key
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=model, api_key=api_key, temperature=temperature)

    raise LLMConfigError(f"Unknown LLM provider: {provider!r}")
