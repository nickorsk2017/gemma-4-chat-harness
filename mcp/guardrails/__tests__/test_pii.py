"""TASK A2: every required type is redacted, the notice is verbatim, nothing leaks."""

import pytest

from guardrails.detectors import pii
from guardrails.schemas.verdict import PII_NOTICE_TEMPLATE
from guardrails.tests.fixtures.corpus import PII_CASES


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


def test_snils_checksum_rejects_a_random_nine_digit_run():
    """Without the checksum this layer would redact ordinary numbers as SNILS."""
    assert pii.valid_snils("112-233-445 95")
    assert not pii.valid_snils("111-111-111 11")


def test_inn_checksum_both_forms():
    assert pii.valid_inn("500100732259")   # 12-digit, person
    assert pii.valid_inn("7830002293")     # 10-digit, legal entity
    assert not pii.valid_inn("1234567890")


def test_leak_detection_ignores_placeholders_but_catches_values():
    """A returned <PHONE_NUMBER> is fine; the actual number coming back is not."""
    assert pii.leaked_types("ваш номер <PHONE_NUMBER>", ["PHONE_NUMBER"]) == []
    assert pii.leaked_types("ваш номер +7 916 123-45-67", ["PHONE_NUMBER"]) == ["PHONE_NUMBER"]


# --- what the checksums buy (TASK A9-1) ---------------------------------------------
# These are the reason the layer is regex *plus* a validator. Without them every digit
# run of the right length is "personal data", and a redactor that eats order numbers and
# error codes gets turned off by whoever has to read the output.


@pytest.mark.parametrize(
    "text,why",
    [
        ("заказ 1234567890123456 отгружен", "16 digits that fail Luhn"),
        ("карта 4111 1111 1111 1112 срок", "one digit off a real card"),
        ("код 123456789 подтвердите", "9 digits, not a SNILS"),
        ("счёт DE89370400440532013001 тут", "one digit off a real IBAN"),
        ("артикул 500100732250 на складе", "12 digits that fail the INN check"),
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
    result = pii.redact("телефон +7 916 123-45-67 и почта a.b@c.io")
    assert sorted(result.types) == ["EMAIL_ADDRESS", "PHONE_NUMBER"]
    assert "EMAIL_ADDRESS, PHONE_NUMBER" in result.notice
