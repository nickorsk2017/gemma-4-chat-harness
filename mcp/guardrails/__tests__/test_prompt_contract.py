"""What the judge is *asked* for (2026-08-05-pii-redaction-orchestration R5).

Every other test stubs the judge, which is right — a third-party model's opinion is not
this repo's behaviour. But that leaves the prompt itself untested, and the prompt is where
the reported defect lived: the model was explicitly told not to report passports, because
the pattern layer was assumed to have removed them already. It had not. Nothing about that
regression would have failed a test, so these assert the instruction directly.
"""

from guardrails.prompts import JUDGE_SYSTEM
from guardrails.services.pipeline import _MODEL_PII_TYPES


def test_the_judge_is_asked_for_identifiers_of_any_country():
    assert "ID_NUMBER" in JUDGE_SYSTEM
    for term in ("passport", "DNI", "national ID"):
        assert term in JUDGE_SYSTEM, f"the prompt names no {term}"


def test_the_judge_is_no_longer_told_to_skip_formatted_values():
    """The exact instruction that caused the miss. If it returns in any form, the model
    goes back to trusting a layer that cannot see a malformed value."""
    assert "Do not list things that have a format" not in JUDGE_SYSTEM
    assert "already removed before you see this text" not in JUDGE_SYSTEM


def test_every_type_the_prompt_offers_is_a_type_the_cascade_accepts():
    """The two halves of the same change. An offered type missing here is silently
    rewritten to PERSON."""
    offered = {"PERSON", "LOCATION", "ID_NUMBER", "OTHER"}
    assert offered <= _MODEL_PII_TYPES
    for name in offered:
        assert name in JUDGE_SYSTEM


def test_the_declaration_is_the_signal_not_the_shape():
    assert "whether or not it is well formed" in JUDGE_SYSTEM
    assert "order id" in JUDGE_SYSTEM  # the counter-example that bounds it


def test_terseness_is_not_injection_evidence():
    """2026-08-05-guardrail-news-false-positive: the reported defect. A short,
    non-English informational ask ("Какие новости?") was scored as injection because
    the clause gave the judge no counter-example, only abstract wording. If this rule
    or its anchor phrase disappears, the model has nothing to weigh again."""
    assert "Terseness is not evidence" in JUDGE_SYSTEM
    assert "Какие новости?" in JUDGE_SYSTEM  # the counter-example that bounds it
