"""Image analysis service.

The attached image is sent to the shared multimodal model (Novita, via
``agent_core.llm.get_llm``) as a base64 data-URL content part, alongside the
prompt, using LangChain. No mock fallback: a missing ``GEMMA_API_KEY`` raises
``LLMConfigError`` on first use.
"""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from agent_core.files import FilePayload
from agent_core.llm import get_llm
from image_analyzer.prompts.vision import ANALYZE_IMAGE
from image_analyzer.schemas.image import ImageAnalysis


async def analyze_image(prompt: str, file: FilePayload) -> ImageAnalysis:
    """Send the image + prompt to the multimodal model and return its answer."""
    message = HumanMessage(
        content=[
            {"type": "text", "text": ANALYZE_IMAGE.format(
                filename=file.filename, prompt=prompt
            )},
            {"type": "image_url", "image_url": {"url": file.data_url()}},
        ]
    )
    reply = await get_llm().ainvoke([message])
    answer = reply.content if isinstance(reply.content, str) else str(reply.content)
    return ImageAnalysis(filename=file.filename, answer=answer)
