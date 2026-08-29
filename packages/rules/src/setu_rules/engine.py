"""The deterministic eligibility engine.

No language model participates in any decision made here. Given the same profile and
the same rule files, this module returns byte-identical output every time — that is
what makes a verdict replayable from `match_runs` months later.

Verdict logic, in order:

  1. Any HARD_BLOCK rule that is definitively true  -> INELIGIBLE
  2. Otherwise, any HARD_BLOCK rule that is UNKNOWN -> NEED_MORE_INFO
  3. Otherwise, any SOFT_WARN rule that is true     -> LIKELY_ELIGIBLE
  4. Otherwise                                      -> ELIGIBLE

Step 2 is the important one. A rule is UNKNOWN when it references a field the citizen
has not given us. We report that as "we need one more fact", never as "you do not
qualify".
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from setu_rules.loader import load_schemes, rules_digest
from setu_rules.models import (
    MatchResult,
    MatchRun,
    Reason,
    Scheme,
    Severity,
    Verdict,
)
from setu_rules.profile import validate_profile
from setu_rules.questions import next_best_question
from setu_rules.safe_eval import UNKNOWN, evaluate_node
from setu_rules.translations import translation_status
from setu_rules.version import ENGINE_VERSION

# Sentinel used when a scheme states no ceiling, so it sorts after any scheme that
# does state one. Larger than the largest figure in the problem statement.
_NO_CEILING = float("inf")


def _message(mapping: dict[str, str], language: str) -> str:
    """Locale lookup with an explicit English fallback.

    Missing translations fall back rather than raising: a citizen reading Marathi still
    gets a correct reason, in English, instead of an error page.
    """
    return mapping.get(language) or mapping.get("en") or ""


def evaluate_scheme(scheme: Scheme, profile: dict[str, Any], language: str = "en") -> MatchResult:
    """Evaluate one scheme against one profile."""
    blocked: list[Reason] = []
    matched: list[Reason] = []
    warnings: list[Reason] = []
    missing: set[str] = set()
    redirect: str | None = None

    hard_rules = [r for r in scheme.rules if r.severity is Severity.HARD_BLOCK]
    decided_hard = 0

    for rule in scheme.rules:
        outcome = evaluate_node(rule.when, profile)

        if outcome is UNKNOWN:
            if rule.severity is Severity.HARD_BLOCK:
                # Only the fields actually absent are worth asking about.
                missing.update(f for f in rule.fields if profile.get(f) is None)
            continue

        if rule.severity is Severity.HARD_BLOCK:
            decided_hard += 1

        if outcome is True:
            reason = Reason(rule.id, _message(rule.message_i18n, language), rule.severity)
            if rule.severity is Severity.HARD_BLOCK:
                blocked.append(reason)
                # First redirect wins; rules are evaluated in file order, which is
                # authored most-specific-first.
                if redirect is None and rule.suggest_instead:
                    redirect = rule.suggest_instead
            else:
                warnings.append(reason)
                if redirect is None and rule.suggest_instead:
                    redirect = rule.suggest_instead
        elif rule.satisfied_i18n:
            matched.append(
                Reason(rule.id, _message(rule.satisfied_i18n, language), rule.severity)
            )

    if blocked:
        verdict = Verdict.INELIGIBLE
        confidence = 1.0
    elif missing:
        verdict = Verdict.NEED_MORE_INFO
        confidence = round(decided_hard / len(hard_rules), 4) if hard_rules else 0.0
    elif warnings:
        verdict = Verdict.LIKELY_ELIGIBLE
        confidence = 1.0
    else:
        verdict = Verdict.ELIGIBLE
        confidence = 1.0

    return MatchResult(
        scheme_code=scheme.code,
        official_name=scheme.official_name,
        family=scheme.family,
        verdict=verdict,
        confidence=confidence,
        matched_because=tuple(matched),
        blocked_because=tuple(blocked),
        warnings=tuple(warnings),
        missing_fields=tuple(sorted(missing)),
        # No figure for a scheme the citizen cannot have — an amount on a blocked card
        # is an anchor they will remember and we would be inventing it.
        indicative_amount=(
            None if verdict is Verdict.INELIGIBLE else indicative_amount(scheme, profile)
        ),
        indicative_interest_band=(
            (scheme.limits.interest_rate_min, scheme.limits.interest_rate_max)
            if scheme.limits.interest_rate_min is not None
            and scheme.limits.interest_rate_max is not None
            else None
        ),
        max_funding_pct=scheme.limits.max_funding_pct,
        redirect_suggestion=redirect,
        needs_verification=scheme.provenance.needs_verification,
        provenance=scheme.provenance,
        translation_status=translation_status(language),
    )


def indicative_amount(scheme: Scheme, profile: dict[str, Any]) -> float | None:
    """The smaller of the scheme's LOAN cap and the funded share of the project cost.

    The loan cap, not the project-cost band: NSFDC will fund a Rs 1,40,000 micro-finance
    unit but lend at most Rs 1,25,000 against it. Using the band here would tell the
    citizen they can borrow Rs 1,26,000, which is false.

    Returns None when the project cost is unknown, rather than showing a figure the
    citizen might anchor on.
    """
    cost = profile.get("project_cost")
    if cost is None:
        return None

    pct = scheme.limits.max_funding_pct
    funded = cost * (pct / 100.0) if pct is not None else float(cost)

    cap = scheme.limits.max_loan_amount
    amount = funded if cap is None else min(funded, float(cap))
    return round(amount, 2)


def _rank_key(result: MatchResult, scheme: Scheme, profile: dict[str, Any]) -> tuple:
    """Pure ranking key: tightest fit, then cheapest, then most generous.

    The trailing scheme_code guarantees a total order, so ranking never depends on
    dict or filesystem iteration order.
    """
    cost = profile.get("project_cost")
    ceiling = scheme.limits.max_project_cost

    if cost is None or ceiling is None:
        headroom = _NO_CEILING
    else:
        headroom = float(ceiling) - float(cost)
        if headroom < 0:
            headroom = _NO_CEILING  # cannot actually fund the ask

    interest = scheme.limits.interest_rate_min
    interest_key = interest if interest is not None else _NO_CEILING

    pct = scheme.limits.max_funding_pct
    funding_key = -(pct if pct is not None else 0.0)

    return (headroom, interest_key, funding_key, result.scheme_code)


_VERDICT_ORDER = {
    Verdict.ELIGIBLE: 0,
    Verdict.LIKELY_ELIGIBLE: 1,
    Verdict.NEED_MORE_INFO: 2,
    Verdict.INELIGIBLE: 3,
}


def evaluate(
    profile: dict[str, Any],
    language: str = "en",
    schemes: tuple[Scheme, ...] | None = None,
) -> list[MatchResult]:
    """Evaluate every scheme and return them in deterministic ranked order.

    Ineligible schemes are returned too, ranked last. The UI shows them greyed out with
    the exact blocking reason — transparency beats hiding.
    """
    validate_profile(profile)
    catalogue = schemes if schemes is not None else load_schemes()
    by_code = {s.code: s for s in catalogue}

    results = [evaluate_scheme(s, profile, language) for s in catalogue]
    results.sort(
        key=lambda r: (_VERDICT_ORDER[r.verdict], *_rank_key(r, by_code[r.scheme_code], profile))
    )

    return [replace(r, rank=i) for i, r in enumerate(results, start=1)]


def run(
    profile: dict[str, Any],
    language: str = "en",
    schemes: tuple[Scheme, ...] | None = None,
) -> MatchRun:
    """Evaluate and wrap the result in the record persisted to `match_runs`."""
    catalogue = schemes if schemes is not None else load_schemes()
    results = evaluate(profile, language, catalogue)
    return MatchRun(
        engine_version=ENGINE_VERSION,
        rules_digest=rules_digest(),
        input_snapshot=dict(sorted(profile.items())),
        results=tuple(results),
        next_question=next_best_question(profile, catalogue),
    )
