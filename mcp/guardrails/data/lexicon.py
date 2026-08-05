"""Curated RU+EN lexicon for the deterministic fast path (PLAN D4).

Terms are stored already normalized (see ``detectors.normalize``) so matching is a
plain substring scan over the folded text. This layer is deliberately blunt: it
exists to resolve the obvious cases cheaply and to hand everything ambiguous to the
judge, not to be the classifier.

MEDICAL_SIGNALS is not a third category — it is the context marker that turns a
drug hit into a ``review`` rather than a block (TASK R13, PLAN D9).
"""

from __future__ import annotations

SEXUAL: tuple[str, ...] = (
    # RU
    "порно", "порнограф", "интим услуг", "секс за деньги", "эротическ",
    "обнаженн", "мастурбац", "оргаз", "половой акт", "секс видео",
    # EN
    "porn", "pornograph", "explicit sex", "erotic", "masturbat", "orgasm",
    "nude photo", "sexual intercourse", "escort service",
)

DRUGS: tuple[str, ...] = (
    # RU — procurement and consumption vocabulary
    # Stem, not the full word: "наркотической" inflects to a "наркотич-" stem, so
    # "наркотик" would miss it. Stops short of "нарко" on purpose — that would also
    # match "наркоз" (anesthesia), which is the opposite of what we want to flag.
    "наркот", "герои", "кокаин", "амфетамин", "метамфетамин", "мефедрон",
    "спайс", "закладк", "марихуан", "гашиш", "лсд", "экстази", "психоделик",
    "где купить траву", "варить мет", "синтез наркот",
    # EN
    # Controlled substances with real clinical use: these fire the category on purpose,
    # and the medical-context check (R13) is what keeps a patient from being refused.
    "морфин", "опиоид", "метадон", "фентанил", "бензодиазепин", "кодеин", "трамадол",
    "morphine", "opioid", "methadone", "fentanyl", "benzodiazepine", "codeine", "tramadol",
    "narcotic", "heroin", "cocaine", "amphetamine", "methamphetamine", "mephedrone",
    "marijuana", "cannabis dealer", "lsd", "ecstasy", "buy weed", "cook meth",
    "drug dealer",
)

# Good-faith clinical / pharmacological context (TASK R13).
MEDICAL_SIGNALS: tuple[str, ...] = (
    # RU
    "врач", "доктор", "рецепт", "дозиров", "побочн", "противопоказан",
    "лечени", "терапи", "препарат", "лекарств", "пациент", "симптом",
    "передозиров", "отмен", "зависимост", "реабилитац", "аптек", "диагноз",
    "взаимодейств", "анестез", "обезболив", "клиническ", "фармаколог",
    # EN
    "doctor", "prescription", "dosage", "side effect", "contraindicat",
    "treatment", "therapy", "medication", "patient", "symptom", "overdose",
    "withdrawal", "addiction treatment", "rehab", "pharmacy", "diagnosis",
    "drug interaction", "anesthesia", "analgesic", "clinical", "pharmacolog",
)
