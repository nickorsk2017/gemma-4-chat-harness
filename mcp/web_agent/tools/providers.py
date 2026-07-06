"""Providers behind web_agent tools. Everything is served by the real gemma LLM
(``google/gemma-4-31b-it`` via the NVIDIA OpenAI-compatible endpoint) through the
shared ``agent_core.llm`` factory. No mock fallback: a missing ``GEMMA_API_KEY``
raises ``LLMConfigError`` on first use."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel

from agent_core.llm import build_chat_model
from web_agent.config import settings
from web_agent.prompts.generate import NEWS_GEN, PAGE_GEN, WEATHER_GEN
from web_agent.schemas.web import NewsResult, Weather, WebPage

_model: BaseChatModel | None = None


def _chat_model() -> BaseChatModel:
    global _model
    if _model is None:
        _model = build_chat_model(
            provider=settings.llm_provider,
            model=settings.llm_model,
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )
    return _model


async def fetch_news(query: str, limit: int) -> NewsResult:
    structured = _chat_model().with_structured_output(NewsResult)
    return await structured.ainvoke(NEWS_GEN.format(query=query, limit=limit))


async def fetch_weather(location: str) -> Weather:
    structured = _chat_model().with_structured_output(Weather)
    return await structured.ainvoke(WEATHER_GEN.format(location=location))


async def fetch_page(url: str) -> WebPage:
    structured = _chat_model().with_structured_output(WebPage)
    return await structured.ainvoke(PAGE_GEN.format(url=url))
