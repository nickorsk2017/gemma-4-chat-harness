"""The flow (TASK A3-4): PII masking library -> keyword pre-filter -> model.

Ordering is not cosmetic. Masking runs first so that no layer downstream — including the
model, a network call to a third party — ever sees a phone number or a passport. The
keyword layer runs second and **decides nothing** (PLAN D12): its hits are evidence, and
their one job is to aim the model's bounded window at the passage that matters, which is
what keeps whole-document checks from being truncated blindly from the front.

The model decides. There is no deterministic short-circuit left, which is the accepted
cost of TASK A3-2 and the reason the fail policy below carries more weight than it used
to: when the model has no opinion, nothing else has one either.

Two outcomes (TASK A3-5): allowed or blocked. The medical path answers and appends a
disclaimer rather than holding the turn.
"""

from __future__ import annotations

import logging
import re
import time

from guardrails.config import settings
from guardrails.detectors import judge as judge_layer
from guardrails.detectors import pii
from guardrails.detectors.lexicon import LexiconResult, scan
from guardrails.schemas.verdict import (
    MEDICAL_DISCLAIMER,
    PII_NOTICE_TEMPLATE,
    Redaction,
    Category,
    CheckRequest,
    Decision,
    Direction,
    Surface,
    Verdict,
)
from guardrails.services.fence import fence

log = logging.getLogger("guardrails.decision")

UNTRUSTED = (Surface.DOCUMENT, Surface.TOOL_RESULT)


def _evidence(lex: LexiconResult) -> set[str]:
    return {term for terms in lex.hits.values() for term in terms}


def _log(request: CheckRequest, verdict: Verdict) -> None:
    """Decision log (TASK R11): types and scores only, never a redacted value."""
    if not settings.log_decisions:
        return
    log.info(
        "guardrail decision",
        extra={
            "source": request.source,
            "surface": request.surface.value,
            "direction": request.direction.value,
            "decision": verdict.decision.value,
            "categories": [c.value for c in verdict.categories],
            "scores": verdict.scores,
            "redacted_types": [r.type for r in verdict.redactions],
            "latency_ms": verdict.latency_ms,
        },
    )


def _with_disclaimer(verdict: Verdict, signal: str) -> Verdict:
    """The medical path (TASK A3-5): answer, and say the data may be inaccurate.

    The human in the loop is the doctor reading the answer, not a moderator clearing a
    queue, so nothing is held. The disclaimer joins the PII notice rather than replacing
    it: a redaction that happened does not stop being true because the topic is clinical.
    """
    if not settings.medical_disclaimer:
        return verdict
    verdict.decision = Decision.ALLOWED
    verdict.notice = "\n\n".join(x for x in (verdict.notice, MEDICAL_DISCLAIMER) if x)
    verdict.reason = signal
    return verdict


# The four the prompt asks for. Anything else is a model slip, not a new type.
#
# ``ID_NUMBER`` and the prompt's identifier clause are one change, not two. The fallback
# below rewrites an unknown type to PERSON, so widening the prompt alone would mask a DNI
# and then report it as somebody's name — wrong in the user's notice and wrong in the
# `known_pii_types` the output gate re-checks against.
_MODEL_PII_TYPES = {"PERSON", "LOCATION", "ID_NUMBER", "OTHER"}
_TYPE = re.compile(r"[^A-Z_]")


def _mask_model_pii(
    verdict: Verdict, items: list[dict[str, str]]
) -> Verdict:
    """Mask the unstructured personal data the model found (TASK A9-1).

    This is the half no pattern can catch — names, addresses — and it is the reason the
    spaCy NER engine is gone rather than replaced: it was a statistical model too, just a
    weaker one carrying an ML stack behind it.

    The honest caveat, recorded where it is implemented: the model *saw* these values in
    order to find them. That is a real difference from the structured types, which are
    masked before any model call. What this buys is that nothing downstream — the answering
    model, the checkpointer, the traces — ever sees them.
    """
    if not settings.pii_model_entities or not items:
        return verdict

    counts: dict[str, int] = {}
    text = verdict.text
    for item in items:
        value = (item.get("text") or "").strip()
        entity = _TYPE.sub("", (item.get("type") or "").upper())
        if entity not in _MODEL_PII_TYPES:
            entity = "PERSON"
        if value and value in text:
            text = text.replace(value, f"<{entity}>")
            counts[entity] = counts.get(entity, 0) + 1
    if not counts:
        return verdict

    verdict.text = text
    merged = {r.type: r.count for r in verdict.redactions}
    for entity, count in counts.items():
        merged[entity] = merged.get(entity, 0) + count
    verdict.redactions = [Redaction(type=t, count=c) for t, c in sorted(merged.items())]
    # The notice is rebuilt, not appended to: it names every type removed, and the model's
    # findings arrive after the deterministic pass has already written one.
    verdict.notice = PII_NOTICE_TEMPLATE.format(types=", ".join(sorted(merged)))
    return verdict


def _neutralise(text: str, spans: list[str]) -> str:
    """Apply the model's edits deterministically (PLAN D13).

    The model returns substrings, not offsets, and the gate does the replacing. Offsets
    would be computed against the *window* the model saw rather than the full text, which
    is the kind of arithmetic that silently redacts the wrong passage on long documents.
    """
    for span in spans:
        if span and span in text:
            text = text.replace(span, "[removed]")
    return text


def _fence_if_untrusted(request: CheckRequest, verdict: Verdict) -> Verdict:
    """Fence what came from a document or a tool, per TASK R4 / A3-6.

    Applied by the gate, not by the caller: callers pass text in and forward what comes
    back. Only on an allowed verdict — blocked text does not travel.
    """
    if request.surface in UNTRUSTED and verdict.decision is Decision.ALLOWED:
        verdict.text, verdict.system_note = fence(verdict.text)
    return verdict


async def check(request: CheckRequest) -> Verdict:
    """Run the flow and return the verdict the caller acts on."""
    started = time.perf_counter()

    # 1. Masking first, so nothing downstream sees raw personal data (TASK R4, R5, A3-3).
    if request.direction is Direction.INPUT:
        pii_result = pii.redact(request.text)
        text, redactions, notice = pii_result.text, pii_result.redactions, pii_result.notice
    else:
        # On the way out we do not re-anonymize the answer wholesale; we check that what
        # was redacted on the way in has not come back as a value (PLAN R-5).
        leaked = pii.leaked_types(request.text, request.known_pii_types)
        if leaked:
            pii_result = pii.redact(request.text)
            text, redactions, notice = pii_result.text, pii_result.redactions, pii_result.notice
        else:
            text, redactions, notice = request.text, [], None

    verdict = Verdict(text=text, redactions=redactions, notice=notice)

    # 2. Keywords: evidence only. No branch below reads this as a decision (PLAN D12).
    lex = scan(text, sexual=settings.check_sexual, drugs=settings.check_drugs)

    # 3. The model decides.
    opinion = await judge_layer.judge(text, _evidence(lex), request.surface)

    if opinion is None:
        return _finish(request, _no_opinion(request, verdict, lex), started)

    verdict.scores = opinion.scores
    verdict.categories = sorted(set(opinion.categories), key=lambda c: c.value)
    verdict.text = _neutralise(verdict.text, opinion.neutralise)
    verdict = _mask_model_pii(verdict, opinion.pii)

    if Category.INJECTION in verdict.categories:
        verdict.decision = Decision.BLOCKED
        verdict.reason = opinion.reason or "prompt injection"
        return _finish(request, verdict, started)

    if Category.DRUGS in verdict.categories and opinion.medical_context:
        verdict = _with_disclaimer(
            verdict, opinion.reason or "drug category in medical context"
        )
        return _finish(request, _fence_if_untrusted(request, verdict), started)

    if verdict.categories:
        verdict.decision = Decision.BLOCKED
        verdict.reason = opinion.reason or "policy violation"
        return _finish(request, verdict, started)

    verdict.decision = Decision.ALLOWED
    return _finish(request, _fence_if_untrusted(request, verdict), started)


def _no_opinion(request: CheckRequest, verdict: Verdict, lex: LexiconResult) -> Verdict:
    """What an absent model means (TASK R8), now that nothing else decides.

    This is the one place the keyword layer influences an outcome, and only because there
    is nothing else left: with the model down, its medical signal is the difference
    between refusing a patient and answering one. Everywhere else its hits are evidence.
    """
    if lex.is_medical_context and Category.DRUGS in lex.categories:
        return _with_disclaimer(
            verdict, "drug category in medical context; model unavailable"
        )
    if request.direction is Direction.INPUT:
        verdict.decision = Decision.BLOCKED  # fail-closed on input (TASK R8)
        verdict.reason = "model unavailable"
    return verdict


def _finish(request: CheckRequest, verdict: Verdict, started: float) -> Verdict:
    verdict.latency_ms = int((time.perf_counter() - started) * 1000)
    _log(request, verdict)
    return verdict
