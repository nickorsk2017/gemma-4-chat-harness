"""Image analysis service.

The attached image is sent to the shared multimodal model (Novita, via
``agent_core.llm.get_llm``) as a base64 data-URL content part, alongside the
prompt, using LangChain. No mock fallback: a missing ``GEMMA_API_KEY`` raises
``LLMConfigError`` on first use.

The model's answer is gated on its way out (PLAN D1). This is the only agent whose
input never meets a gate — the image bytes go straight to the vision model — so the
answer is the first and only text representation of what the picture contains, and
this call site is the sole enforcement point for that modality.
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage

from agent_core.files import FilePayload
from agent_core.guardrails import IMAGE_REJECTED, check_output
from agent_core.llm import get_llm
from image_analyzer.prompts.vision import ANALYZE_IMAGE
from image_analyzer.schemas.image import ImageAnalysis

log = logging.getLogger("image_analyzer.services.analyze_service")


async def analyze_image(prompt: str, file: FilePayload) -> ImageAnalysis:
    """Send the image + prompt to the multimodal model, gate the answer, return it.

    The gate sits after the answer is flattened to ``str`` (PLAN D2): what is gated and
    what is returned are then the same value, not two derivations of one reply.

    A blocked answer is **returned, not raised** (PLAN D3). ``doc_analyzer`` raises, and
    its tool's blanket ``except`` turns that into an error envelope — correct there,
    wrong here: a verdict is not an agent failure, so the refusal travels in a normal
    ``ImageAnalysis`` and the tool's ``AgentResponse.ok`` path is untouched.

    The verdict is used as binary allow/block (PLAN D4). ``verdict.text`` is deliberately
    not substituted: on the output path it is a redaction of our own answer, and this
    agent's scope is block-only. ``thread_id`` is not passed (PLAN D5) — the tool
    signature carries none, and inventing one is worse than correlating by ``source``.

    No ``try``/``except`` around the gate call: the retry ladder and the fail-open
    verdict belong to ``agent_core.guardrails``, and catching here would make this a
    second owner of that policy.
    """
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

    verdict = await check_output(answer, source="image_analyzer")
    if not verdict.allowed:
        # Categories, not content: the answer is exactly what must not be logged.
        log.warning(
            "image answer blocked by the output gate (file=%s categories=%s)",
            file.filename,
            verdict.categories,
        )
        return ImageAnalysis(filename=file.filename, answer=IMAGE_REJECTED)
    return ImageAnalysis(filename=file.filename, answer=answer)
