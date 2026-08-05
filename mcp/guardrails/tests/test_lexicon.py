"""A1 coverage at the fast-path layer: every banned case must at least be seen."""

import pytest

from guardrails.data.lexicon import MEDICAL_SIGNALS
from guardrails.detectors.lexicon import scan
from guardrails.schemas.verdict import Category
from guardrails.tests.fixtures.corpus import BANNED, BENIGN, MEDICAL, MEDICAL_CLEAN


@pytest.mark.parametrize("text,category,tag", BANNED, ids=[f"{c}-{t}" for _, c, t in BANNED])
def test_banned_corpus_is_detected(text, category, tag):
    result = scan(text)
    assert Category(category) in result.categories, f"missed ({tag}): {text!r}"


@pytest.mark.parametrize("text", BENIGN)
def test_benign_corpus_is_clean(text):
    assert scan(text).categories == []


@pytest.mark.parametrize("text,signal", MEDICAL, ids=[s for _, s in MEDICAL])
def test_medical_cases_carry_both_a_category_and_a_signal(text, signal):
    """R13 needs both: the category is what would block, the signal is what holds it."""
    result = scan(text)
    assert Category.DRUGS in result.categories, f"no drug term in {text!r}"
    assert result.is_medical_context, f"no medical signal in {text!r}"


@pytest.mark.parametrize("text", MEDICAL_CLEAN)
def test_clinical_questions_without_a_substance_trip_nothing(text):
    assert scan(text).categories == []


def test_medical_signal_list_is_not_empty():
    assert len(MEDICAL_SIGNALS) > 10
