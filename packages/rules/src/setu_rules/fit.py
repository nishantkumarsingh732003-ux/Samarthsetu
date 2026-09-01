"""Why a scheme ranked where it did, in components a citizen can argue with.

`engine.evaluate` ranks on this score. That is the point of showing it: a number that
does not drive the order explains nothing, and the specification asks the citizen to be
able to see *why* scheme A ranked above scheme B.

Determinism is preserved by what sits underneath it. The sort key is
`(verdict, -fit.total, *_rank_key, scheme_code)` — so two schemes tying on a rounded
float fall through to rule-derived facts and finally to the scheme code, never to the
order files came off a filesystem. The float is allowed to decide precisely because it
is never the last word.

**What is deliberately absent: partner availability.** The specification lists it as a
ranking component, and it is a real signal — but this package is pure, has no database,
and its output is stamped into `match_runs` as the reproducibility record. A score that
moved when a branch paused intake would make a stored decision unreplayable, which is the
one property the whole architecture exists to preserve. Partner availability is answered
where it belongs: on the routing screen, per partner, with its own breakdown.
"""

from __future__ import annotations

from typing import Any

from setu_rules.models import (
    FitComponent,
    FitScore,
    MatchResult,
    Scheme,
    Verdict,
    round_half_up,
)

# Shares of the total. They sum to 1.0, asserted by a test rather than by hope.
WEIGHTS: dict[str, float] = {
    "purpose_fit": 0.30,
    "amount_fit": 0.25,
    "category_fit": 0.20,
    "cost_of_credit": 0.15,
    "information": 0.10,
}

# The family that funds a course rather than an enterprise.
_EDUCATION = "EDUCATION_LOAN"

# NSFDC concessional credit sits in a 6.5-8% band, so 6.5% scores 100 and 8% scores 0 —
# a spread the citizen actually feels over the life of the loan.
_CHEAPEST_RATE = 6.5
_DEAREST_RATE = 8.0

# A project using more than this share of the ceiling has little room if costs rise.
_COMFORTABLE_SHARE = 0.80


def _clamp(value: float) -> float:
    return round_half_up(max(0.0, min(100.0, value)), 1)


def _purpose_fit(scheme: Scheme, profile: dict[str, Any]) -> FitComponent:
    """Does this scheme fund the thing they actually want to do?

    The heaviest weight, because funding the wrong *kind* of thing is the misrouting
    this project exists to prevent — it is what sends a workshop owner to a
    micro-finance counter.
    """
    weight = WEIGHTS["purpose_fit"]
    sector = profile.get("project_sector")
    is_education_scheme = str(scheme.family) == _EDUCATION

    if sector is None:
        return FitComponent(
            "purpose_fit", 50.0, weight, "We do not know yet what the money is for."
        )

    wants_education = sector == "EDUCATION"
    if wants_education == is_education_scheme:
        return FitComponent(
            "purpose_fit",
            100.0,
            weight,
            "This scheme funds a course."
            if wants_education
            else "This scheme funds an enterprise project.",
        )
    return FitComponent(
        "purpose_fit",
        0.0,
        weight,
        "This scheme funds a course, and you asked about a business."
        if is_education_scheme
        else "This scheme funds a business, and you asked about studies.",
    )


def _amount_fit(scheme: Scheme, profile: dict[str, Any]) -> FitComponent:
    """Does the amount sit comfortably inside the band, or scrape its ceiling?

    A project at 98% of a ceiling is technically eligible and practically fragile: one
    revised quotation and it is out. A scheme with room left scores higher.
    """
    weight = WEIGHTS["amount_fit"]
    cost = profile.get("project_cost")
    floor = scheme.limits.min_project_cost
    ceiling = scheme.limits.max_project_cost

    if cost is None:
        return FitComponent("amount_fit", 50.0, weight, "We do not know the amount yet.")

    cost = float(cost)
    if ceiling is not None and cost > float(ceiling):
        return FitComponent(
            "amount_fit",
            0.0,
            weight,
            f"Rs {cost:,.0f} is above this scheme's Rs {float(ceiling):,.0f} ceiling.",
        )
    if floor is not None and cost < float(floor):
        return FitComponent(
            "amount_fit",
            0.0,
            weight,
            f"Rs {cost:,.0f} is below this scheme's Rs {float(floor):,.0f} floor.",
        )
    if ceiling is None:
        return FitComponent(
            "amount_fit", 90.0, weight, "This scheme sets no ceiling on the cost of the course."
        )

    used = cost / float(ceiling)
    score = (
        100.0
        if used <= _COMFORTABLE_SHARE
        else 100.0 - ((used - _COMFORTABLE_SHARE) / (1 - _COMFORTABLE_SHARE)) * 40.0
    )
    detail = (
        f"Rs {cost:,.0f} sits well inside the Rs {float(ceiling):,.0f} ceiling."
        if used <= _COMFORTABLE_SHARE
        else f"Rs {cost:,.0f} is close to the Rs {float(ceiling):,.0f} ceiling, so there "
        "is little room if costs rise."
    )
    return FitComponent("amount_fit", _clamp(score), weight, detail)


def _category_fit(result: MatchResult) -> FitComponent:
    """Are the scheme's own hard requirements satisfied, or still open?

    Read off the verdict rather than recomputed, so this component can never disagree
    with the decision it is explaining.
    """
    weight = WEIGHTS["category_fit"]
    if result.verdict is Verdict.ELIGIBLE:
        return FitComponent("category_fit", 100.0, weight, "You meet every requirement.")
    if result.verdict is Verdict.LIKELY_ELIGIBLE:
        return FitComponent(
            "category_fit", 80.0, weight, "You meet every requirement, with a note to check."
        )
    if result.verdict is Verdict.NEED_MORE_INFO:
        missing = len(result.missing_fields)
        return FitComponent(
            "category_fit",
            50.0,
            weight,
            f"{missing} more answers needed to be sure."
            if missing != 1
            else "One more answer is needed to be sure.",
        )
    blocker = (
        result.blocked_because[0].message if result.blocked_because else "A rule blocks this."
    )
    return FitComponent("category_fit", 0.0, weight, blocker)


def _cost_of_credit(scheme: Scheme) -> FitComponent:
    """Cheaper money and a larger covered share are worth more to the citizen.

    Two thirds interest, one third funding share: the rate is paid for years, while the
    funding share only decides how much has to be found up front.
    """
    weight = WEIGHTS["cost_of_credit"]
    rate = scheme.limits.interest_rate_min
    pct = scheme.limits.max_funding_pct

    if rate is None:
        rate_score = 50.0
    else:
        span = _DEAREST_RATE - _CHEAPEST_RATE
        rate_score = _clamp(100.0 - ((float(rate) - _CHEAPEST_RATE) / span) * 100.0)

    funding_score = _clamp(float(pct)) if pct is not None else 50.0
    score = _clamp(rate_score * (2 / 3) + funding_score * (1 / 3))

    parts = []
    if rate is not None:
        parts.append(f"{float(rate):g}% interest")
    if pct is not None:
        parts.append(f"covers up to {float(pct):g}% of the cost")
    detail = (" and ".join(parts) + ".").capitalize() if parts else "Terms are not published."
    return FitComponent("cost_of_credit", score, weight, detail)


def _information(result: MatchResult) -> FitComponent:
    """How much of this scheme's own contract we can actually see.

    Not a property of the scheme — a property of how much the citizen has told us. It
    carries the smallest weight because it says more about the conversation than about
    the fit, but showing it stops the other four looking more certain than they are.
    """
    weight = WEIGHTS["information"]
    missing = len(result.missing_fields)
    if missing == 0:
        return FitComponent("information", 100.0, weight, "We have everything this scheme asks.")
    return FitComponent(
        "information",
        _clamp(100.0 - missing * 25.0),
        weight,
        f"{missing} answers still missing." if missing != 1 else "One answer still missing.",
    )


def fit_score(scheme: Scheme, result: MatchResult, profile: dict[str, Any]) -> FitScore:
    """The full breakdown for one scheme. Pure, deterministic, no I/O."""
    components = (
        _purpose_fit(scheme, profile),
        _amount_fit(scheme, profile),
        _category_fit(result),
        _cost_of_credit(scheme),
        _information(result),
    )
    return FitScore(
        total=round_half_up(sum(c.contribution for c in components), 1),
        components=components,
    )
