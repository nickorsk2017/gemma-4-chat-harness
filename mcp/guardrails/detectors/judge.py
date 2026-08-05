"""The model layer — the only layer that decides anything (TASK A3-2).

Two things this module refuses to inherit from ``agent_core.llm``: the 90s per-attempt
timeout and the retry. A gate that hangs for 90s is indistinguishable from a gate that is
down, which would make TASK R8's fail-closed path fire on healthy traffic (PLAN R-1).

It also refuses to see unbounded text: whole documents come through here, so the model is
shown a bounded window centred on whatever the keyword layer flagged (PLAN R-2, D12).
That is the keyword layer's entire remaining job — aiming this window. It decides nothing.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

from guardrails.config import settings
from guardrails.prompts import JUDGE_SYSTEM, JUDGE_USER
from guardrails.schemas.verdict import Category, Surface


@dataclass
class JudgeVerdict:
    categories: list[Category]
    scores: dict[str, float]
    medical_context: bool
    reason: str
    neutralise: list[str] = field(default_factory=list)
    # Unstructured personal data the model found: [{"text": ..., "type": ...}].
    # The structured types never reach here — they are masked before the call.
    pii: list[dict[str, str]] = field(default_factory=list)


_model = None


def _get_model():
    global _model
    if _model is None:
        from langchain_openai import ChatOpenAI

        if not settings.judge_api_key:
            raise RuntimeError("GEMMA_API_KEY is not set; the judge cannot run")
        import os

        _model = ChatOpenAI(
            model=settings.judge_model or os.environ.get("GEMMA_MODEL", "google/gemma-4-31b-it"),
            api_key=settings.judge_api_key,
            base_url=settings.judge_base_url,
            temperature=0.0,
            timeout=settings.judge_timeout_s,
            max_retries=0,
        )
    return _model


def _window(text: str, evidence: set[str]) -> str:
    """Bound what the model sees, centred on the terms the keyword layer flagged.

    Truncating from the front would routinely cut away the very passage that triggered
    the check, so the window is built around the first hit instead. With no hits there is
    no anchor and the head is all we can honestly show.
    """
    cap = settings.judge_max_chars
    if cap <= 0 or len(text) <= cap:
        return text
    lowered = text.casefold()
    anchor = min((lowered.find(t) for t in evidence if lowered.find(t) >= 0), default=-1)
    if anchor < 0:
        return text[:cap]
    start = max(0, anchor - cap // 2)
    return text[start : start + cap]


def _enabled(category: Category) -> bool:
    return {
        Category.SEXUAL: settings.check_sexual,
        Category.DRUGS: settings.check_drugs,
        Category.INJECTION: settings.check_injection,
    }[category]


def _parse(raw: str) -> JudgeVerdict:
    """Read the model's JSON verdict; anything unparseable is 'nothing found'.

    Deliberate: a malformed reply must not manufacture a category. The caller decides
    what an absent opinion means (TASK R8) — and with no deterministic layer left to fall
    back on, that decision is the whole fail policy.
    """
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text.split("\n", 1)[-1] if "\n" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        return JudgeVerdict([], {}, False, "unparseable judge reply")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return JudgeVerdict([], {}, False, "unparseable judge reply")

    scores: dict[str, float] = {}
    for category in Category:
        try:
            scores[category.value] = float(data.get(category.value, 0.0))
        except (TypeError, ValueError):
            scores[category.value] = 0.0
    categories = [
        c for c in Category if _enabled(c) and scores[c.value] >= settings.judge_threshold
    ]
    neutralise = [s for s in (data.get("neutralise") or []) if isinstance(s, str) and s]
    pii = [
        {"text": str(item.get("text", "")), "type": str(item.get("type", ""))}
        for item in (data.get("pii") or [])
        if isinstance(item, dict) and item.get("text")
    ]
    return JudgeVerdict(
        categories=categories,
        scores=scores,
        medical_context=bool(data.get("medical_context", False)),
        reason=str(data.get("reason", ""))[:300],
        neutralise=neutralise[:20],
        pii=pii[:50],
    )


async def judge(
    text: str,
    evidence: set[str] | None = None,
    surface: Surface = Surface.PROMPT,
) -> JudgeVerdict | None:
    """Ask the model. Returns None when it is disabled, unavailable or too slow.

    None means "no opinion", not "clean".
    """
    if not settings.judge_enabled:
        return None
    from langchain_core.messages import HumanMessage, SystemMessage

    window = _window(text, evidence or set())
    try:
        async with asyncio.timeout(settings.judge_timeout_s):
            reply = await _get_model().ainvoke(
                [
                    SystemMessage(content=JUDGE_SYSTEM),
                    HumanMessage(
                        content=JUDGE_USER.format(text=window, surface=surface.value)
                    ),
                ]
            )
    except (TimeoutError, Exception):  # noqa: BLE001 - never raises across the cascade
        return None
    content = reply.content if isinstance(reply.content, str) else str(reply.content)
    return _parse(content)
