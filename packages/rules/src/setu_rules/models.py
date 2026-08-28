"""Value objects returned by the engine.

Everything here is a frozen dataclass with a `to_dict()`, because these objects are
persisted verbatim into `match_runs.results` and must serialise identically every time
for the golden snapshot tests and for decision replay.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Verdict(StrEnum):
    ELIGIBLE = "ELIGIBLE"
    LIKELY_ELIGIBLE = "LIKELY_ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    NEED_MORE_INFO = "NEED_MORE_INFO"


class Severity(StrEnum):
    HARD_BLOCK = "HARD_BLOCK"
    SOFT_WARN = "SOFT_WARN"


class Family(StrEnum):
    MICRO_FINANCE = "MICRO_FINANCE"
    TERM_LOAN = "TERM_LOAN"
    EDUCATION_LOAN = "EDUCATION_LOAN"


@dataclass(frozen=True, slots=True)
class Reason:
    """One rule's contribution to a verdict, quotable in the UI."""

    rule_id: str
    message: str
    severity: Severity

    def to_dict(self) -> dict[str, Any]:
        return {"rule_id": self.rule_id, "message": self.message, "severity": str(self.severity)}


@dataclass(frozen=True, slots=True)
class OpenQuestion:
    """A figure that is still unresolved, recorded rather than guessed."""

    field: str
    question: str

    def to_dict(self) -> dict[str, Any]:
        return {"field": self.field, "question": self.question}


@dataclass(frozen=True, slots=True)
class Provenance:
    source: str | None
    source_url: str | None
    circular_ref: str | None
    effective_from: str | None
    last_verified_on: str | None
    needs_verification: bool
    verification_note: str | None = None
    open_questions: tuple[OpenQuestion, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "source_url": self.source_url,
            "circular_ref": self.circular_ref,
            "effective_from": self.effective_from,
            "last_verified_on": self.last_verified_on,
            "needs_verification": self.needs_verification,
            "verification_note": self.verification_note,
            "open_questions": [q.to_dict() for q in self.open_questions],
        }


@dataclass(frozen=True, slots=True)
class Limits:
    """Two different ceilings that must never be conflated.

    NSFDC states an eligibility *band* on what the unit/project may cost, and separately
    a cap on the *loan* it will advance. For the Micro Finance Scheme those are
    Rs 1,40,000 and Rs 1,25,000 respectively — so 90% of a Rs 1,40,000 project is
    Rs 1,26,000, which exceeds the loan cap. Using one number for both overstates what
    a citizen can actually borrow.
    """

    # Eligibility band on the cost of the unit or course.
    min_project_cost: float | None
    max_project_cost: float | None
    # Ceiling on the loan itself.
    max_loan_amount: float | None
    max_funding_pct: float | None
    interest_rate_min: float | None
    interest_rate_max: float | None
    tenure_months: int | None
    moratorium_months: int | None


@dataclass(frozen=True, slots=True)
class Rule:
    id: str
    severity: Severity
    when_source: str
    when: dict[str, Any]
    message_i18n: dict[str, str]
    satisfied_i18n: dict[str, str]
    suggest_instead: str | None
    fields: frozenset[str]


@dataclass(frozen=True, slots=True)
class Scheme:
    code: str
    official_name: str
    name_i18n: dict[str, str]
    family: Family
    provenance: Provenance
    limits: Limits
    rules: tuple[Rule, ...]
    pending_translations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MatchResult:
    scheme_code: str
    official_name: str
    family: Family
    verdict: Verdict
    confidence: float
    matched_because: tuple[Reason, ...] = ()
    blocked_because: tuple[Reason, ...] = ()
    warnings: tuple[Reason, ...] = ()
    missing_fields: tuple[str, ...] = ()
    indicative_amount: float | None = None
    indicative_interest_band: tuple[float, float] | None = None
    max_funding_pct: float | None = None
    redirect_suggestion: str | None = None
    needs_verification: bool = False
    provenance: Provenance | None = None
    rank: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme_code": self.scheme_code,
            "official_name": self.official_name,
            "family": str(self.family),
            "verdict": str(self.verdict),
            "confidence": self.confidence,
            "matched_because": [r.to_dict() for r in self.matched_because],
            "blocked_because": [r.to_dict() for r in self.blocked_because],
            "warnings": [r.to_dict() for r in self.warnings],
            "missing_fields": list(self.missing_fields),
            "indicative_amount": self.indicative_amount,
            "indicative_interest_band": (
                list(self.indicative_interest_band) if self.indicative_interest_band else None
            ),
            "max_funding_pct": self.max_funding_pct,
            "redirect_suggestion": self.redirect_suggestion,
            "needs_verification": self.needs_verification,
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "rank": self.rank,
        }


@dataclass(frozen=True, slots=True)
class NextQuestion:
    """The single field that would resolve the most currently-undecided rules."""

    field_name: str
    question_i18n: dict[str, str]
    kind: str
    choices: tuple[str, ...] | None
    resolves_rules: tuple[str, ...]
    resolves_schemes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field_name,
            "question_i18n": dict(self.question_i18n),
            "kind": self.kind,
            "choices": list(self.choices) if self.choices else None,
            "resolves_rules": list(self.resolves_rules),
            "resolves_schemes": list(self.resolves_schemes),
        }


@dataclass(frozen=True, slots=True)
class MatchRun:
    """The complete, replayable record of one engine execution."""

    engine_version: str
    rules_digest: str
    input_snapshot: dict[str, Any]
    results: tuple[MatchResult, ...]
    next_question: NextQuestion | None = None
    unmatched_notes: tuple[str, ...] = field(default=())

    def to_dict(self) -> dict[str, Any]:
        return {
            "engine_version": self.engine_version,
            "rules_digest": self.rules_digest,
            "input_snapshot": self.input_snapshot,
            "results": [r.to_dict() for r in self.results],
            "next_question": self.next_question.to_dict() if self.next_question else None,
        }
