"""PII layer: detect and redact, never reject (TASK R4, R5, A9-1).

Two kinds of personal data, and only one of them belongs to a library.

**Structured** — email, card, IBAN — is a pattern, plus a checksum where the format has
one. Deterministic, offline, and testable by the strongest assertion available: the
original value appears nowhere in the output. A sixteen-digit run is not a card; without
the check digit the false-positive rate on ordinary numbers makes redaction worse than
useless. That is this module.

**Unstructured** — names, addresses, identity and document numbers — has no pattern to
match and is not here. It is the model's job (see ``detectors/judge.py``), because the
only alternative was spaCy, and spaCy is a statistical model too: same class of guarantee
as an LLM, weaker on Russian, and carrying presidio, thinc, blis and two model downloads
behind it.

Presidio is gone with it — not by preference but by construction: `presidio-analyzer`
depends on spaCy unconditionally, so the two could not be separated. What it actually
contributed here was four regex recognizers and a score threshold; the overlap resolution
and the replacement were always this file's own.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from guardrails.config import settings
from guardrails.schemas.verdict import PII_NOTICE_TEMPLATE, Redaction

ENTITIES = ["EMAIL_ADDRESS", "CREDIT_CARD", "IBAN_CODE"]


# --- checksum validators ------------------------------------------------------------

def _digits(value: str) -> list[int]:
    return [int(c) for c in value if c.isdigit()]


def valid_luhn(value: str) -> bool:
    """Card numbers, mod 10. Without it every 16-digit run is a "card"."""
    d = _digits(value)
    if not 13 <= len(d) <= 19:
        return False
    total, parity = 0, len(d) % 2
    for i, digit in enumerate(d):
        if i % 2 == parity:
            digit *= 2
            if digit > 9:
                digit -= 9
        total += digit
    return total % 10 == 0


def valid_iban(value: str) -> bool:
    """IBAN mod-97: move the first four characters to the end, letters to digits, == 1."""
    cleaned = re.sub(r"[^A-Za-z0-9]", "", value).upper()
    if not 15 <= len(cleaned) <= 34:
        return False
    rearranged = cleaned[4:] + cleaned[:4]
    try:
        numeric = "".join(
            str(int(c, 36)) if c.isalpha() else c for c in rearranged
        )
    except ValueError:
        return False
    return int(numeric) % 97 == 1


# --- recognizers ----------------------------------------------------------------------

_EMAIL_PATTERN = r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
# Both of these end on a digit/character rather than an optional separator: a trailing
# `[ -]?` inside the repeat eats the space after the value, so the replacement silently
# glues the placeholder to the next word.
_CARD_PATTERN = r"\b\d(?:[ \-]?\d){12,18}\b"
_IBAN_PATTERN = r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]){11,30}\b"


@dataclass(frozen=True)
class _Recognizer:
    entity: str
    pattern: re.Pattern[str]
    score: float
    validator: Callable[[str], bool] | None = None


# Order is not significance — overlaps are resolved by span, below — but the scores are.
# They are the same values the previous pattern set carried, so the score threshold keeps
# meaning what it meant.
RECOGNIZERS: list[_Recognizer] = [
    _Recognizer("EMAIL_ADDRESS", re.compile(_EMAIL_PATTERN), 0.9),
    _Recognizer("IBAN_CODE", re.compile(_IBAN_PATTERN), 0.7, valid_iban),
    _Recognizer("CREDIT_CARD", re.compile(_CARD_PATTERN), 0.7, valid_luhn),
]


@dataclass(frozen=True)
class _Span:
    start: int
    end: int
    entity: str
    score: float


def _scan(text: str) -> list[_Span]:
    """Find every candidate span, validate it, and score it.

    **A passing checksum promotes the span to certainty.** This is not a tweak — it is
    what makes the base scores mean anything. Card and IBAN carry 0.7 because a digit run
    of that shape is weak evidence on its own; once the check digits agree it is no longer
    a guess, and the score threshold must not throw it away. (Presidio did the same thing
    through `validate_result`; porting the numbers without the promotion is how validated
    types silently stop being detected.)
    """
    spans: list[_Span] = []
    for rec in RECOGNIZERS:
        for match in rec.pattern.finditer(text):
            value = match.group(0)
            score = rec.score
            if rec.validator is not None:
                if not rec.validator(value):
                    continue
                score = 1.0
            if score < settings.pii_score_threshold:
                continue
            spans.append(_Span(match.start(), match.end(), rec.entity, score))
    return spans


def warmup() -> None:
    """Kept as the startup hook, now trivial.

    It used to build presidio's analyzer, which took tens of seconds — longer than the
    callers' client timeout, so the first request after every deploy tripped the
    fail-closed path. Regexes compile at import, so there is nothing left to warm; the
    call stays because ``main.py`` is entitled to a startup contract that does not
    change every time the layer underneath does.
    """
    _scan("warmup")


# --- public API -----------------------------------------------------------------------

@dataclass
class PiiResult:
    """Redacted text plus what was removed. The values themselves are never kept."""

    text: str
    redactions: list[Redaction]

    @property
    def types(self) -> list[str]:
        return [r.type for r in self.redactions]

    @property
    def notice(self) -> str | None:
        """The TASK R5 string, or None when nothing was redacted."""
        if not self.redactions:
            return None
        return PII_NOTICE_TEMPLATE.format(types=", ".join(sorted(self.types)))


def mask_spans(text: str, spans: list[tuple[int, int, str]]) -> tuple[str, dict[str, int]]:
    """Replace ``(start, end, entity)`` spans with ``<ENTITY>``, right to left.

    Right to left because replacing left to right invalidates every offset after the
    first substitution.
    """
    counts: dict[str, int] = {}
    out = text
    for start, end, entity in sorted(spans, key=lambda s: s[0], reverse=True):
        out = f"{out[:start]}<{entity}>{out[end:]}"
        counts[entity] = counts.get(entity, 0) + 1
    return out, counts


def redact(text: str) -> PiiResult:
    """Replace every detected PII span with ``<TYPE>`` and report what was replaced."""
    if not settings.pii_enabled or not text:
        return PiiResult(text=text, redactions=[])

    found = _scan(text)
    if not found:
        return PiiResult(text=text, redactions=[])

    # Overlaps must be resolved before replacement, or a nested match corrupts the
    # placeholder written by its neighbour. Earliest span wins; among spans starting
    # together, the longer one, then the more confident one — a card pattern and an IBAN
    # pattern can cover the same characters and the wrong label would be recorded.
    ordered = sorted(found, key=lambda s: (s.start, -(s.end - s.start), -s.score))
    kept: list[_Span] = []
    last_end = -1
    for span in ordered:
        if span.start >= last_end:
            kept.append(span)
            last_end = span.end

    out, counts = mask_spans(text, [(s.start, s.end, s.entity) for s in kept])
    redactions = [Redaction(type=t, count=c) for t, c in sorted(counts.items())]
    return PiiResult(text=out, redactions=redactions)


_PLACEHOLDER = re.compile(r"<([A-Z_]+)>")


def leaked_types(text: str, known_types: list[str]) -> list[str]:
    """Types that were redacted on input but reappear as real values on output.

    A placeholder coming back is fine — the model echoing the *value* is not.

    Structured types only: this is the deterministic scanner, so a name the model masked
    on the way in is not re-checked on the way out. Named that here rather than left to
    be discovered.
    """
    if not known_types:
        return []
    stripped = _PLACEHOLDER.sub(" ", text)
    found = {r.type for r in redact(stripped).redactions}
    return sorted(found & set(known_types))
