"""Deterministic lexicon layer — the fast path (PLAN D3, D4).

The terms are folded through exactly the same normalization as the text before either
is matched. Skipping that is the classic way this layer silently stops working: fold
only the text and every english term stops matching, because homoglyph folding rewrites
latin letters into their cyrillic twins on one side of the comparison and not the other.

Three matching forms are searched and their hits unioned:

* ``normalize``      — case, accents, homoglyphs, repeats folded; separators kept as spaces
* ``transliterate``  — latin-script russian folded back to cyrillic
* ``collapsed``      — the normalized form with every separator removed, which is what
  catches ``к-о-к-а-и-н`` and ``b u y  w e e d``

Aho-Corasick scans all terms of a form in one pass, so term count is free at request
time. ``pyahocorasick`` is the intended path; the pure-python fallback keeps the layer
working where the wheel is unavailable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from guardrails.data.lexicon import DRUGS, MEDICAL_SIGNALS, SEXUAL
from guardrails.detectors.normalize import normalize, transliterate
from guardrails.schemas.verdict import Category

try:  # pragma: no cover - import-shape branch
    import ahocorasick

    _HAVE_AC = True
except ImportError:  # pragma: no cover
    _HAVE_AC = False

_SEPARATORS = re.compile(r"\s+")


def collapse(text: str) -> str:
    """The normalized form with separators removed."""
    return _SEPARATORS.sub("", normalize(text))


def _forms(text: str) -> tuple[str, str, str]:
    return normalize(text), transliterate(text), collapse(text)


def _automaton(terms: set[str]):
    terms = {t for t in terms if t}
    if not _HAVE_AC:
        return terms
    automaton = ahocorasick.Automaton()
    for term in terms:
        automaton.add_word(term, term)
    automaton.make_automaton()
    return automaton


def _build(terms: tuple[str, ...]) -> tuple:
    """One automaton per matching form, with the terms folded the same way."""
    return (
        _automaton({normalize(t) for t in terms}),
        _automaton({transliterate(t) for t in terms}),
        _automaton({collapse(t) for t in terms}),
    )


def _hits(automaton, haystack: str) -> set[str]:
    if not haystack:
        return set()
    if not _HAVE_AC:
        return {t for t in automaton if t in haystack}
    return {found for _, found in automaton.iter(haystack)}


def _scan_all(automata: tuple, forms: tuple[str, str, str]) -> set[str]:
    found: set[str] = set()
    for automaton, form in zip(automata, forms):
        found |= _hits(automaton, form)
    return found


_AUTOMATA = {
    Category.SEXUAL: _build(SEXUAL),
    Category.DRUGS: _build(DRUGS),
}
_MEDICAL = _build(MEDICAL_SIGNALS)


@dataclass
class LexiconResult:
    """What the fast path knows on its own."""

    hits: dict[Category, set[str]] = field(default_factory=dict)
    medical_signals: set[str] = field(default_factory=set)

    @property
    def categories(self) -> list[Category]:
        return [c for c, terms in self.hits.items() if terms]

    @property
    def max_hits(self) -> int:
        return max((len(t) for t in self.hits.values()), default=0)

    @property
    def is_medical_context(self) -> bool:
        return bool(self.medical_signals)


def scan(text: str, *, sexual: bool = True, drugs: bool = True) -> LexiconResult:
    """Scan every matching form of `text` and union the hits (TASK R9)."""
    forms = _forms(text)
    enabled = {Category.SEXUAL: sexual, Category.DRUGS: drugs}

    hits: dict[Category, set[str]] = {}
    for category, automata in _AUTOMATA.items():
        if not enabled[category]:
            continue
        found = _scan_all(automata, forms)
        if found:
            hits[category] = found

    return LexiconResult(hits=hits, medical_signals=_scan_all(_MEDICAL, forms))
