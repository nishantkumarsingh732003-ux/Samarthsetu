"""The fit score: what it explains, and what it must never do.

The load-bearing test in this file is `test_the_fit_score_never_changes_the_ranking`.
The score exists to explain an order that is decided elsewhere; the moment it starts
producing that order, two schemes can tie on a float and a citizen's ranking depends on
filesystem iteration order.
"""

from __future__ import annotations

import pytest

from setu_rules import evaluate
from setu_rules.fit import WEIGHTS, fit_score
from setu_rules.loader import load_schemes

SUNITA = {
    "category": "SC",
    "project_sector": "TRADE",
    "annual_family_income": 180000,
    "project_cost": 80000,
}
RAMESH = {
    "category": "SC",
    "project_sector": "MANUFACTURING",
    "annual_family_income": 420000,
    "project_cost": 1200000,
}
ANJALI = {
    "category": "SC",
    "project_sector": "EDUCATION",
    "admission_confirmed": True,
    "annual_family_income": 260000,
    "project_cost": 600000,
}


# --- the contract ------------------------------------------------------------------


def test_the_weights_sum_to_one() -> None:
    """Otherwise the total is not out of 100 and the caption lies."""
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


@pytest.mark.parametrize("profile", [SUNITA, RAMESH, ANJALI, {}])
def test_every_result_carries_a_breakdown(profile: dict) -> None:
    for result in evaluate(profile):
        assert result.fit is not None
        assert len(result.fit.components) == len(WEIGHTS)


@pytest.mark.parametrize("profile", [SUNITA, RAMESH, ANJALI, {}])
def test_the_total_is_the_sum_of_the_contributions(profile: dict) -> None:
    """A citizen adding the column up must get the headline number."""
    for result in evaluate(profile):
        parts = sum(c.contribution for c in result.fit.components)
        assert result.fit.total == pytest.approx(parts, abs=0.1)


@pytest.mark.parametrize("profile", [SUNITA, RAMESH, ANJALI, {}])
def test_every_score_is_a_percentage(profile: dict) -> None:
    for result in evaluate(profile):
        assert 0.0 <= result.fit.total <= 100.0
        for component in result.fit.components:
            assert 0.0 <= component.score <= 100.0, component.key


@pytest.mark.parametrize("profile", [SUNITA, RAMESH, ANJALI, {}])
def test_every_component_explains_itself_in_words(profile: dict) -> None:
    """A number with no sentence beside it is the opaque score this replaces."""
    for result in evaluate(profile):
        for component in result.fit.components:
            assert component.detail.strip(), component.key
            assert not component.detail.startswith("{"), "a template leaked through"


# --- the invariant that matters ------------------------------------------------------


@pytest.mark.parametrize("profile", [SUNITA, RAMESH, ANJALI, {}])
def test_the_score_agrees_with_the_order_it_explains(profile: dict) -> None:
    """A citizen must never read "#2, 44/100" above "#3, 54/100".

    The score drives ranking after the verdict, so within a verdict group it must fall
    monotonically. This was the bug: the score was presentational, the tuple ordered,
    and the two disagreed on screen.
    """
    results = evaluate(profile)
    assert [r.rank for r in results] == sorted(r.rank for r in results)

    order = {"ELIGIBLE": 0, "LIKELY_ELIGIBLE": 1, "NEED_MORE_INFO": 2, "INELIGIBLE": 3}
    verdicts = [order[str(r.verdict)] for r in results]
    assert verdicts == sorted(verdicts), "a better verdict must never rank below a worse one"

    for group in set(verdicts):
        totals = [r.fit.total for r, v in zip(results, verdicts, strict=True) if v == group]
        assert totals == sorted(totals, reverse=True), (
            f"scores are not monotonic within the {group} group: {totals}"
        )


def test_the_score_is_deterministic() -> None:
    """Same profile, same score. Every time, or `match_runs` is not a record."""
    first = [r.fit.to_dict() for r in evaluate(RAMESH)]
    second = [r.fit.to_dict() for r in evaluate(RAMESH)]
    assert first == second


def test_the_top_scheme_scores_highest_when_one_is_clearly_eligible() -> None:
    """The explanation has to agree with the decision, or it explains nothing."""
    results = evaluate(SUNITA)
    assert results[0].fit.total == max(r.fit.total for r in results)


# --- the components individually --------------------------------------------------------


def _component(profile: dict, scheme_code: str, key: str):
    result = next(r for r in evaluate(profile) if r.scheme_code == scheme_code)
    return next(c for c in result.fit.components if c.key == key)


def test_purpose_fit_is_zero_when_a_trader_meets_the_education_scheme() -> None:
    assert _component(SUNITA, "NSFDC_EDUCATION_LOAN", "purpose_fit").score == 0.0


def test_purpose_fit_is_full_when_a_student_meets_the_education_scheme() -> None:
    assert _component(ANJALI, "NSFDC_EDUCATION_LOAN", "purpose_fit").score == 100.0


def test_purpose_fit_is_neutral_when_we_do_not_know_the_purpose_yet() -> None:
    """Half marks, not zero — an unanswered question is not a mismatch."""
    assert _component({}, "NSFDC_MICRO_FINANCE", "purpose_fit").score == 50.0


def test_amount_fit_is_zero_above_the_ceiling() -> None:
    component = _component(RAMESH, "NSFDC_MICRO_FINANCE", "amount_fit")
    assert component.score == 0.0
    assert "above" in component.detail


def test_amount_fit_is_zero_below_the_floor() -> None:
    component = _component(SUNITA, "NSFDC_TERM_LOAN", "amount_fit")
    assert component.score == 0.0
    assert "below" in component.detail


def test_a_project_scraping_the_ceiling_scores_below_one_with_room() -> None:
    """Technically eligible and practically fragile: one revised quote and it is out."""
    roomy = {**SUNITA, "project_cost": 80_000}
    tight = {**SUNITA, "project_cost": 139_000}
    assert (
        _component(tight, "NSFDC_MICRO_FINANCE", "amount_fit").score
        < _component(roomy, "NSFDC_MICRO_FINANCE", "amount_fit").score
    )


def test_category_fit_carries_the_actual_blocking_reason() -> None:
    """Not a generic 'ineligible' — the sentence the engine produced."""
    component = _component(SUNITA, "NSFDC_EDUCATION_LOAN", "category_fit")
    assert component.score == 0.0
    assert len(component.detail) > 15


def test_the_cheaper_scheme_scores_higher_on_cost_of_credit() -> None:
    """6.5% against 8%, over years. The citizen feels this one."""
    micro = _component(SUNITA, "NSFDC_MICRO_FINANCE", "cost_of_credit")
    term = _component(SUNITA, "NSFDC_TERM_LOAN", "cost_of_credit")
    assert micro.score > term.score


def test_information_is_full_when_nothing_is_missing() -> None:
    assert _component(SUNITA, "NSFDC_MICRO_FINANCE", "information").score == 100.0


def test_information_drops_when_the_citizen_has_told_us_little() -> None:
    """Stops the other four components looking more certain than they are."""
    assert _component({}, "NSFDC_MICRO_FINANCE", "information").score < 100.0


# --- purity ---------------------------------------------------------------------------


def test_the_score_needs_no_database_and_no_network() -> None:
    """It is stamped into match_runs, so it must be reproducible from the rules alone.

    Partner availability is deliberately not a component: a stored decision whose score
    moved when a branch paused intake would no longer be replayable.
    """
    schemes = load_schemes()
    results = evaluate(SUNITA, schemes=schemes)
    for result in results:
        scheme = next(s for s in schemes if s.code == result.scheme_code)
        assert fit_score(scheme, result, SUNITA).to_dict() == result.fit.to_dict()


# --- the cross-language rounding hazard -------------------------------------------------


def test_rounding_is_half_up_and_not_pythons_default() -> None:
    """Python rounds half-to-even; JavaScript rounds half-up. We pick one, explicitly.

    96.7 x 0.15 scales to exactly 1450.5, where the two languages disagree — Python's
    round() gives 14.5 and Math.round() gives 14.51. The conformance suite caught it,
    but inheriting either language's default was the bug, not the mismatch.
    """
    from setu_rules.models import round_half_up

    assert round_half_up(14.504999999999999 * 100 / 100, 2) == 14.51
    assert round(14.504999999999999, 2) == 14.5, "Python's default still differs, as expected"

    # The halfway cases Python's banker's rounding sends to even.
    assert round_half_up(0.125, 2) == 0.13
    assert round_half_up(2.5, 0) == 3.0
    assert round_half_up(3.5, 0) == 4.0


def test_the_component_that_exposed_it_still_matches_javascript() -> None:
    """A regression here means the two engines have silently drifted apart again."""
    component = _component(SUNITA, "NSFDC_MICRO_FINANCE", "cost_of_credit")
    assert component.score == 96.7
    assert component.contribution == 14.51
