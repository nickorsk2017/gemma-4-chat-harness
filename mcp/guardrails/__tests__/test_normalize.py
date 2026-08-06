"""Normalization is what makes TASK R9 possible; test it on its own."""

from guardrails.detectors.normalize import matching_forms, normalize, transliterate


def test_homoglyphs_fold_to_one_form():
    """A latin 'a' inside a cyrillic word must not survive as a different string."""
    assert normalize("нaркотики") == normalize("наркотики")


def test_padding_and_repeats_collapse():
    assert normalize("н-а-р-к-о-т-и-к-и") == "н а р к о т и к и"
    assert normalize("нааааркотики") == normalize("наркотики")


def test_zero_width_characters_are_removed():
    assert normalize("нар​котики") == "нар котики"


def test_transliteration_reaches_cyrillic():
    assert "наркотики" in transliterate("narkotiki")


def test_both_forms_are_offered():
    plain, translit = matching_forms("Kokain")
    assert plain and translit
    assert "кокаин" in translit
