"""Indian numeral parsing.

Every case here is a way a real applicant states an amount. A parser error near
Rs 5,00,000 moves someone across the income ceiling, so the boundary forms are tested
explicitly rather than assumed.
"""

import pytest

from app.services.numerals import normalise_digits, parse_amount, parse_rupees


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # --- plain digits, Indian grouping ---
        ("250000", 250000),
        ("2,50,000", 250000),
        ("5,00,000", 500000),
        ("1,40,000", 140000),
        ("Rs 80,000", 80000),
        ("₹12,00,000", 1200000),
        # --- English scale words ---
        ("2.5 lakh", 250000),
        ("2.5 lakhs", 250000),
        ("2.5 lac", 250000),
        ("5 lakh", 500000),
        ("12 lakh", 1200000),
        ("1 crore", 10000000),
        ("80 thousand", 80000),
        ("five lakh", 500000),
        ("two lakh", 200000),
        # --- romanised Hindi ---
        ("dhai lakh", 250000),
        ("adhai lakh", 250000),
        ("dedh lakh", 150000),
        ("derh lakh", 150000),
        ("sava lakh", 125000),
        ("paune do lakh", 175000),
        ("sadhe teen lakh", 350000),
        ("do lakh", 200000),
        ("teen lakh", 300000),
        ("assi hazaar", 80000),
        ("das hazar", 10000),
        ("ek karod", 10000000),
        # --- Devanagari ---
        ("ढाई लाख", 250000),
        ("डेढ़ लाख", 150000),
        ("सवा लाख", 125000),
        ("पौने दो लाख", 175000),
        ("साढ़े तीन लाख", 350000),
        ("दो लाख", 200000),
        ("पांच लाख", 500000),
        ("अस्सी हजार", 80000),
        ("एक करोड़", 10000000),
        ("२,५०,०००", 250000),
        ("१२००००", 120000),
        # --- compound amounts ---
        ("2 lakh 40 thousand", 240000),
        ("do lakh chalees hazaar", 240000),
        ("दो लाख चालीस हजार", 240000),
        ("1 lakh 20 thousand", 120000),
        # --- embedded in a sentence ---
        ("my yearly income is about 2.5 lakh rupees", 250000),
        ("मेरी सालाना आय ढाई लाख है", 250000),
        ("I need 80 thousand for my vegetable cart", 80000),
        ("saal ka aay do lakh chalees hazaar hai", 240000),
        # --- other Indic digits ---
        ("২,৫০,০০০", 250000),
        ("௧௨௦௦௦௦", 120000),
    ],
)
def test_parses_amount(text: str, expected: float) -> None:
    assert parse_rupees(text) == expected


@pytest.mark.parametrize(
    "text",
    ["", "hello", "no money at all", "मुझे नहीं पता", "vegetable vendor"],
)
def test_returns_none_when_there_is_no_amount(text: str) -> None:
    assert parse_rupees(text) is None


def test_income_ceiling_boundary_forms_all_agree() -> None:
    """Every way of saying five lakh must land exactly on the ceiling, not near it."""
    for text in ("500000", "5,00,000", "5 lakh", "paanch lakh", "पांच लाख", "५,००,०००"):
        assert parse_rupees(text) == 500000, text


def test_micro_finance_band_boundary_forms_all_agree() -> None:
    for text in ("140000", "1,40,000", "1.4 lakh", "एक लाख चालीस हजार"):
        assert parse_rupees(text) == 140000, text


def test_digit_normalisation_leaves_non_numeric_commas_alone() -> None:
    """"Nagpur, Maharashtra" must not become "NagpurMaharashtra"."""
    assert normalise_digits("Nagpur, Maharashtra") == "Nagpur, Maharashtra"
    assert normalise_digits("2,50,000") == "250000"


def test_evidence_span_points_at_the_words_that_were_read() -> None:
    parsed = parse_amount("my yearly income is about 2.5 lakh rupees")
    assert parsed is not None
    assert "2.5 lakh" in parsed.evidence
    assert parsed.start < parsed.end


def test_parse_is_deterministic() -> None:
    assert {parse_rupees("ढाई लाख") for _ in range(20)} == {250000}


def test_fraction_modifier_applies_to_the_following_number_not_the_scale() -> None:
    """paune do lakh is 1.75 lakh, not 2 lakh minus a quarter rupee."""
    assert parse_rupees("paune do lakh") == 175000
    assert parse_rupees("sava do lakh") == 225000
