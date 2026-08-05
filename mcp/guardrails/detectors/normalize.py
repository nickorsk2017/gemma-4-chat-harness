"""Text normalization — runs before every other layer (TASK R9, PLAN D4).

Without this the lexicon is trivially defeated: a single latin ``a`` inside a
cyrillic word, a zero-width space, or transliteration all slip straight past exact
matching. Normalization is lossy on purpose — its output is used for *matching only*,
never for redaction offsets or for anything the user sees.
"""

from __future__ import annotations

import re
import unicodedata

# Latin glyphs that render as their cyrillic twins (and vice versa). Folded to a
# single cyrillic form so mixed-script spellings collapse onto one key.
_HOMOGLYPHS = str.maketrans(
    {
        "a": "а", "b": "ь", "c": "с", "e": "е", "h": "н", "k": "к", "m": "м",
        "o": "о", "p": "р", "t": "т", "x": "х", "y": "у",
        "A": "а", "B": "в", "C": "с", "E": "е", "H": "н", "K": "к", "M": "м",
        "O": "о", "P": "р", "T": "т", "X": "х", "Y": "у",
        "0": "о", "3": "з", "4": "ч", "6": "б",
    }
)

# Multi-character transliterations first; single characters are handled after.
_TRANSLIT_DIGRAPHS = (
    ("shch", "щ"), ("sch", "щ"), ("zh", "ж"), ("kh", "х"), ("ts", "ц"),
    ("ch", "ч"), ("sh", "ш"), ("yu", "ю"), ("ya", "я"), ("yo", "ё"),
    ("iu", "ю"), ("ia", "я"), ("je", "е"),
)
_TRANSLIT_SINGLES = str.maketrans(
    {
        "a": "а", "b": "б", "v": "в", "g": "г", "d": "д", "e": "е", "z": "з",
        "i": "и", "j": "й", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о",
        "p": "п", "r": "р", "s": "с", "t": "т", "u": "у", "f": "ф", "h": "х",
        "c": "ц", "y": "ы", "w": "в", "q": "к", "x": "кс",
    }
)

# Padding used to break up words: zero-width chars, separators, repeated punctuation.
_PADDING = re.compile(r"[​-‏⁠﻿\W_]+", flags=re.UNICODE)
_REPEATS = re.compile(r"(.)\1{2,}")


def _strip_marks(text: str) -> str:
    """Drop combining marks left over from NFKD (accents, diacritic obfuscation)."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Fold `text` to the matching form used by the lexicon layer."""
    folded = _strip_marks(text.casefold())
    folded = folded.translate(_HOMOGLYPHS)
    folded = _REPEATS.sub(r"\1", folded)
    return _PADDING.sub(" ", folded).strip()


def transliterate(text: str) -> str:
    """Second matching form: latin-script russian folded back to cyrillic.

    Produced in addition to :func:`normalize`, not instead of it — folding is
    ambiguous, so both forms are searched and hits are unioned.
    """
    out = _strip_marks(text.casefold())
    for digraph, cyr in _TRANSLIT_DIGRAPHS:
        out = out.replace(digraph, cyr)
    out = out.translate(_TRANSLIT_SINGLES)
    out = _REPEATS.sub(r"\1", out)
    return _PADDING.sub(" ", out).strip()


def matching_forms(text: str) -> tuple[str, str]:
    """Both forms the lexicon should be searched against."""
    return normalize(text), transliterate(text)
