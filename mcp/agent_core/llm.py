from __future__ import annotations

import os

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

NOVITA_BASE_URL = "https://api.novita.ai/openai"
DEFAULT_MODEL = os.environ.get("GEMMA_MODEL", "google/gemma-4-31b-it")

# One temperature for the whole app.
DEFAULT_TEMPERATURE = 0.5

DEFAULT_REQUEST_TIMEOUT_S = 90.0


def _request_timeout() -> float:
    return float(os.environ.get("LLM_REQUEST_TIMEOUT_S", DEFAULT_REQUEST_TIMEOUT_S))


class LLMConfigError(RuntimeError):
    """The LLM is misconfigured (missing GEMMA_API_KEY)."""


_shared_model: BaseChatModel | None = None


def build_chat_model(
    *,
    model: str = DEFAULT_MODEL,
    api_key: str | None = None,
    base_url: str = NOVITA_BASE_URL,
    temperature: float = DEFAULT_TEMPERATURE,
) -> BaseChatModel:
    global _shared_model
    if _shared_model is not None:
        return _shared_model

    key = api_key or os.environ.get("GEMMA_API_KEY")
    if not key:
        raise LLMConfigError(
            "GEMMA_API_KEY is not set. The whole app uses one Novita provider; "
            "there is no mock fallback."
        )

    _shared_model = ChatOpenAI(
        model=model,
        api_key=key,
        base_url=base_url,
        temperature=temperature,
        timeout=_request_timeout(),
        max_retries=1,
    )
    return _shared_model


def get_llm() -> BaseChatModel:
    """Convenience accessor for the shared provider."""
    return build_chat_model()
