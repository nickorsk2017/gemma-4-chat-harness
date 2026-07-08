"""Provider behind the image_analyzer tool.

The attached image is sent to the real multimodal gemma model
(``google/gemma-4-31b-it`` via Novita) as a base64 data-URL content part,
alongside the prompt, using LangChain. No mock fallback: a missing
``GEMMA_API_KEY`` raises ``LLMConfigError`` on first use.
"""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from agent_core.files import FilePayload
from agent_core.llm import build_chat_model
from image_analyzer.config import settings
from image_analyzer.prompts.vision import ANALYZE_IMAGE
from image_analyzer.schemas.image import ImageAnalysis

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


async def analyze_image(prompt: str, file: FilePayload) -> ImageAnalysis:
    """Send the image + prompt to the multimodal gemma model and return its answer."""
    message = HumanMessage(
        content=[
            {"type": "text", "text": ANALYZE_IMAGE.format(
                filename=file.filename, prompt=prompt
            )},
            {"type": "image_url", "image_url": {"url": file.data_url()}},
        ]
    )
    reply = await _chat_model().ainvoke([message])
    answer = reply.content if isinstance(reply.content, str) else str(reply.content)
    return ImageAnalysis(filename=file.filename, answer=answer)
