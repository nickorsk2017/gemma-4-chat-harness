"""TASK A2: every required type is redacted, the notice is verbatim, nothing leaks."""

import pytest

from guardrails.detectors import pii
from guardrails.schemas.verdict import PII_NOTICE_TEMPLATE
from guardrails.__tests__.fixtures.corpus import PII_CASES


@pytest.mark.parametrize("entity,text,value", PII_CASES, ids=[c[0] for c in PII_CASES])
def test_each_type_is_redacted(entity, text, value):
    result = pii.redact(text)
    assert entity in result.types, f"{entity} not detected in {text!r}"


@pytest.mark.parametrize("entity,text,value", PII_CASES, ids=[c[0] for c in PII_CASES])
def test_original_value_never_survives(entity, text, value):
    """The point of the whole layer: the value must not be in what leaves the service."""
    result = pii.redact(text)
    assert value not in result.text
    # Nor may it hide in the structured report.
    assert all(value not in r.type for r in result.redactions)


def test_notice_is_produced_verbatim():
    result = pii.redact("телефон +7 916 123-45-67 и почта a@b.com")
    assert result.notice == PII_NOTICE_TEMPLATE.format(types=", ".join(sorted(result.types)))
    assert result.notice.startswith("Note: the user's personal data (")
    assert result.notice.endswith("was not passed to the system, per policy.")


def test_clean_text_produces_no_notice():
    result = pii.redact("расскажи про погоду")
    assert result.redactions == []
    assert result.notice is None


@pytest.mark.parametrize(
    "text",
    [
        "мой телефон +7 916 123-45-67, перезвоните",
        "паспорт серия 45 05 № 123456 выдан ОВД",
        "мой снилс 112-233-445 95 для справки",
        "инн 500100732259 для договора",
    ],
)
def test_removed_types_are_not_detected_deterministically(text):
    """Phone, RU passport, SNILS and INN are no longer part of the pattern layer."""
    assert pii.redact(text).types == []


def test_leak_detection_ignores_placeholders_but_catches_values():
    """A returned <EMAIL_ADDRESS> is fine; the actual address coming back is not."""
    assert pii.leaked_types("ваша почта <EMAIL_ADDRESS>", ["EMAIL_ADDRESS"]) == []
    assert pii.leaked_types("ваша почта a.b@c.io", ["EMAIL_ADDRESS"]) == ["EMAIL_ADDRESS"]


# --- what the checksums buy (TASK A9-1) ---------------------------------------------
# These are the reason the layer is regex *plus* a validator. Without them every digit
# run of the right length is "personal data", and a redactor that eats order numbers and
# error codes gets turned off by whoever has to read the output.


@pytest.mark.parametrize(
    "text,why",
    [
        ("заказ 1234567890123456 отгружен", "16 digits that fail Luhn"),
        ("карта 4111 1111 1111 1112 срок", "one digit off a real card"),
        ("счёт DE89370400440532013001 тут", "one digit off a real IBAN"),
    ],
)
def test_a_number_that_fails_its_checksum_is_not_personal_data(text, why):
    assert pii.redact(text).types == [], why


def test_the_placeholder_does_not_eat_the_surrounding_spacing():
    """A pattern ending on an optional separator swallows the space after the value and
    glues the placeholder to the next word. Cheap to get wrong, invisible in a type list."""
    out = pii.redact("карта 4111 1111 1111 1111 срок до 05/28").text
    assert "<CREDIT_CARD> срок" in out
    out = pii.redact("счёт DE89370400440532013000 в банке").text
    assert "<IBAN_CODE> в банке" in out


def test_two_types_in_one_text_are_both_named():
    result = pii.redact("карта 4111 1111 1111 1111 и почта a.b@c.io")
    assert sorted(result.types) == ["CREDIT_CARD", "EMAIL_ADDRESS"]
    assert "CREDIT_CARD, EMAIL_ADDRESS" in result.notice
