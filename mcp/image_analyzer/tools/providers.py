"""Providers behind image_analyzer tools. All three tools run through the real
multimodal gemma model (``google/gemma-4-31b-it`` via the NVIDIA endpoint): the
image is sent as a base64 data-URL content part and the answer is parsed into
the domain schemas. No mock fallback: a missing ``GEMMA_API_KEY`` raises
``LLMConfigError`` on first use."""

from __future__ import annotations

import base64
from pathlib import Path

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import HumanMessage

from agent_core.llm import build_chat_model
from image_analyzer.config import settings
from image_analyzer.prompts.vision import DESCRIBE_IMAGE, DETECT_OBJECTS, OCR_IMAGE
from image_analyzer.schemas.image import Caption, DetectionResult, OcrResult

_MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
         ".webp": "image/webp", ".gif": "image/gif"}

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


def _image_part(path: str) -> dict:
    mime = _MIME.get(Path(path).suffix.lower(), "image/jpeg")
    b64 = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}}


async def _vision_invoke(prompt: str, path: str, schema: type):
    message = HumanMessage(content=[{"type": "text", "text": prompt}, _image_part(path)])
    structured = _chat_model().with_structured_output(schema)
    return await structured.ainvoke([message])


async def describe_image(path: str) -> Caption:
    return await _vision_invoke(DESCRIBE_IMAGE.format(path=path), path, Caption)


async def detect_objects(path: str, min_confidence: float) -> DetectionResult:
    result: DetectionResult = await _vision_invoke(
        DETECT_OBJECTS.format(path=path), path, DetectionResult
    )
    result.detections = [d for d in result.detections if d.confidence >= min_confidence]
    return result


async def ocr_image(path: str, lang: str) -> OcrResult:
    return await _vision_invoke(OCR_IMAGE.format(path=path, lang=lang), path, OcrResult)
