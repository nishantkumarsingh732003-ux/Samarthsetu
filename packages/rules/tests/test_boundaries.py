"""Boundary values on every figure the problem statement actually states.

Off-by-one errors here are the difference between a citizen getting a loan and being
told to go away, so each threshold is tested at the limit and one rupee either side.
"""

import pytest

from setu_rules import Verdict, evaluate

BASE = {
    "category": "SC",
    "project_sector": "TRADE",
    "annual_family_income": 200000,
    "project_cost": 100000,
}


def verdict_for(code: str, **overrides) -> Verdict:
    profile = {**BASE, **overrides}
    return next(r.verdict for r in evaluate(profile) if r.scheme_code == code)


def blocked_rules(code: str, **overrides) -> set[str]:
    profile = {**BASE, **overrides}
    result = next(r for r in evaluate(profile) if r.scheme_code == code)
    return {r.rule_id for r in result.blocked_because}


# ------------------------------------------------- income ceiling: Rs 5,00,000 exactly


@pytest.mark.parametrize(
    "code", ["NSFDC_MICRO_FINANCE", "NSFDC_TERM_LOAN", "NSFDC_EDUCATION_LOAN"]
)
def test_income_exactly_at_ceiling_is_allowed(code: str) -> None:
    """"up to Rs 5,00,000" includes Rs 5,00,000."""
    overrides = {"annual_family_income": 500000}
    if code == "NSFDC_EDUCATION_LOAN":
        overrides |= {"project_sector": "EDUCATION", "admission_confirmed": True}
    assert "EL_INCOME_CEILING" not in blocked_rules(code, **overrides)
    assert "MF_INCOME_CEILING" not in blocked_rules(code, **overrides)
    assert "TL_INCOME_CEILING" not in blocked_rules(code, **overrides)


def test_income_one_rupee_over_ceiling_blocks() -> None:
    assert verdict_for("NSFDC_MICRO_FINANCE", annual_family_income=500001) is Verdict.INELIGIBLE
    assert "MF_INCOME_CEILING" in blocked_rules("NSFDC_MICRO_FINANCE", annual_family_income=500001)


def test_income_one_rupee_under_ceiling_passes() -> None:
    assert verdict_for("NSFDC_MICRO_FINANCE", annual_family_income=499999) is Verdict.ELIGIBLE


# -------------------------------------------- micro finance ceiling: Rs 1,40,000 exactly


def test_project_cost_exactly_at_micro_finance_ceiling_is_allowed() -> None:
    """Rs 1,40,000 is inside the band, but 90% of it exceeds the Rs 1,25,000 loan cap,
    so the citizen is eligible *with* a warning that they must fund the difference."""
    assert verdict_for("NSFDC_MICRO_FINANCE", project_cost=140000) is Verdict.LIKELY_ELIGIBLE
    assert not blocked_rules("NSFDC_MICRO_FINANCE", project_cost=140000)


def test_project_cost_one_rupee_over_micro_finance_ceiling_blocks() -> None:
    assert verdict_for("NSFDC_MICRO_FINANCE", project_cost=140001) is Verdict.INELIGIBLE
    assert "MF_PROJECT_COST_BAND" in blocked_rules("NSFDC_MICRO_FINANCE", project_cost=140001)


def test_micro_finance_block_redirects_to_term_loan() -> None:
    """The anti-misrouting feature: we say where to go, not just no."""
    profile = {**BASE, "project_cost": 140001}
    result = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    assert result.redirect_suggestion == "NSFDC_TERM_LOAN"


# ------------------------------------------------ term loan ceiling: Rs 50,00,000 exactly


def test_project_cost_exactly_at_term_loan_ceiling_is_allowed() -> None:
    assert verdict_for("NSFDC_TERM_LOAN", project_cost=5000000) is Verdict.ELIGIBLE


def test_project_cost_one_rupee_over_term_loan_ceiling_blocks() -> None:
    assert verdict_for("NSFDC_TERM_LOAN", project_cost=5000001) is Verdict.INELIGIBLE


def test_term_loan_blocks_at_its_floor_and_redirects_down() -> None:
    """NSFDC: term loans are for "units costing more than Rs 1.40 lakh". At exactly
    Rs 1,40,000 the project belongs to Micro Finance, and we say so."""
    profile = {**BASE, "project_cost": 140000}
    result = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_TERM_LOAN")
    assert result.verdict is Verdict.INELIGIBLE
    assert "TL_PROJECT_COST_FLOOR" in {r.rule_id for r in result.blocked_because}
    assert result.redirect_suggestion == "NSFDC_MICRO_FINANCE"


def test_term_loan_floor_boundary_at_140001_is_eligible() -> None:
    profile = {**BASE, "project_cost": 140001}
    result = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_TERM_LOAN")
    assert result.verdict is Verdict.ELIGIBLE
    assert result.warnings == ()


def test_the_two_schemes_partition_the_cost_line_with_no_gap_or_overlap() -> None:
    """Every project cost must be claimed by exactly one enterprise scheme."""
    for cost in (1, 139999, 140000, 140001, 5000000, 5000001):
        profile = {**BASE, "project_cost": cost}
        open_to = {
            r.scheme_code
            for r in evaluate(profile)
            if r.verdict is not Verdict.INELIGIBLE
            and r.scheme_code in {"NSFDC_MICRO_FINANCE", "NSFDC_TERM_LOAN"}
        }
        expected = 0 if cost > 5000000 else 1
        assert len(open_to) == expected, f"cost {cost} matched {open_to}"


# ------------------------------------------------------------------- indicative amount


def test_indicative_amount_is_capped_by_the_scheme_ceiling() -> None:
    """A Rs 2,00,000 project is outside the micro finance band entirely."""
    profile = {**BASE, "project_cost": 200000}
    micro = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    term = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_TERM_LOAN")
    assert micro.verdict is Verdict.INELIGIBLE  # over the band
    assert term.indicative_amount == 180000.0


def test_indicative_amount_is_ninety_percent_when_under_the_loan_cap() -> None:
    profile = {**BASE, "project_cost": 100000}
    micro = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    assert micro.indicative_amount == 90000.0


def test_indicative_amount_uses_the_loan_cap_not_the_project_band() -> None:
    """The bug this distinction exists to prevent: 90% of Rs 1,40,000 is Rs 1,26,000,
    but the Micro Finance Scheme lends at most Rs 1,25,000."""
    profile = {**BASE, "project_cost": 140000}
    micro = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    assert micro.indicative_amount == 125000.0
    assert "MF_LOAN_CAP_BINDS" in {r.rule_id for r in micro.warnings}


def test_loan_cap_boundary_is_exact() -> None:
    """Rs 1,25,000 / 0.9 = Rs 1,38,888.89, so Rs 1,38,888 still gets the full 90%."""
    below = {**BASE, "project_cost": 138888}
    at = {**BASE, "project_cost": 138889}
    micro_below = next(r for r in evaluate(below) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    micro_at = next(r for r in evaluate(at) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    assert micro_below.warnings == ()
    assert micro_below.indicative_amount == 124999.2
    assert {r.rule_id for r in micro_at.warnings} == {"MF_LOAN_CAP_BINDS"}
    assert micro_at.indicative_amount == 125000.0


def test_ineligible_schemes_show_no_indicative_amount() -> None:
    profile = {**BASE, "annual_family_income": 900000}
    for result in evaluate(profile):
        assert result.verdict is Verdict.INELIGIBLE
        assert result.indicative_amount is None


def test_education_loan_amount_is_the_full_funded_share_below_its_cap() -> None:
    """No band is stated on course cost, and Rs 5,40,000 is far under the Rs 40 lakh cap."""
    profile = {
        "category": "SC",
        "project_sector": "EDUCATION",
        "admission_confirmed": True,
        "annual_family_income": 260000,
        "project_cost": 600000,
    }
    edu = next(r for r in evaluate(profile) if r.scheme_code == "NSFDC_EDUCATION_LOAN")
    assert edu.indicative_amount == 540000.0  # 90% of 6,00,000, uncapped
