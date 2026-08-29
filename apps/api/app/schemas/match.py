"""Request and response models for matching and routing.

Profile fields mirror `setu_rules.profile.FIELDS`; the engine validates them again on
the way in, so a field added to the rule contract without a schema change is rejected
loudly rather than silently ignored.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LANGUAGES = Literal["en", "hi", "mr", "bn", "ta", "te"]


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    profile: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Partial or complete citizen profile. Unknown keys are rejected; missing "
            "keys yield NEED_MORE_INFO rather than a refusal."
        ),
        examples=[
            {
                "category": "SC",
                "project_sector": "TRADE",
                "annual_family_income": 180000,
                "project_cost": 80000,
            }
        ],
    )
    language: LANGUAGES = "en"
    citizen_id: str | None = Field(
        default=None, description="Links the run to a stored citizen, when one exists."
    )


class ReasonOut(BaseModel):
    rule_id: str
    message: str
    severity: str


class MatchResultOut(BaseModel):
    scheme_code: str
    official_name: str
    family: str
    verdict: str
    confidence: float
    matched_because: list[ReasonOut]
    blocked_because: list[ReasonOut]
    warnings: list[ReasonOut]
    missing_fields: list[str]
    indicative_amount: float | None
    indicative_interest_band: list[float] | None
    max_funding_pct: float | None
    redirect_suggestion: str | None
    needs_verification: bool
    provenance: dict[str, Any] | None
    rank: int | None
    # "verified" | "draft" | "fallback" — whether a speaker of the requested language
    # has read this copy. A UI must be able to badge unreviewed eligibility reasons.
    translation_status: str = "verified"


class NextQuestionOut(BaseModel):
    field: str
    question_i18n: dict[str, str]
    kind: str
    choices: list[str] | None
    resolves_rules: list[str]
    resolves_schemes: list[str]


class MatchResponse(BaseModel):
    match_run_id: str
    engine_version: str
    rules_digest: str
    input_snapshot: dict[str, Any]
    results: list[MatchResultOut]
    next_question: NextQuestionOut | None


class RouteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_code: str = Field(examples=["NSFDC_MICRO_FINANCE"])
    amount: float = Field(gt=0, examples=[90000])
    lat: float | None = Field(default=None, ge=-90, le=90, examples=[21.1458])
    lng: float | None = Field(default=None, ge=-180, le=180, examples=[79.0882])
    district: str | None = Field(default=None, examples=["Nagpur"])
    match_run_id: str | None = Field(
        default=None,
        description="Ties this routing call to the eligibility decision that led to it.",
    )


class ScoreComponent(BaseModel):
    value: Any
    unit: str
    score: float
    weight: float
    contribution: float


class RoutedPartnerOut(BaseModel):
    partner_id: str
    name: str
    type: str
    parent_org: str | None
    ifsc: str | None
    address: str | None
    district: str
    state: str
    pincode: str | None
    contact: dict[str, Any]
    lat: float | None
    lng: float | None
    distance_km: float | None
    avg_turnaround_days: int | None
    active_load: int | None
    min_ticket: float | None
    max_ticket: float | None
    score: float
    score_breakdown: dict[str, ScoreComponent]
    rank: int | None


class WhyNotOut(BaseModel):
    partner_id: str
    name: str
    type: str
    district: str
    distance_km: float | None
    reason_code: str
    reason: str


class RouteResponse(BaseModel):
    routing_version: str
    scheme_code: str
    scheme_name: str
    amount_requested: float
    origin: dict[str, float] | None
    district: str | None
    weights: dict[str, float]
    candidates_considered: int
    eligible_partner_count: int
    partners: list[RoutedPartnerOut]
    why_not: list[WhyNotOut]
    data_disclaimer: str
    cached: bool = False


class AuthorisationOut(BaseModel):
    scheme_code: str
    scheme_name: str
    family: str
    min_ticket: float | None
    max_ticket: float | None
    is_currently_accepting: bool
    avg_turnaround_days: int | None
    active_load: int | None
    service_districts: list[str]


class PartnerDetailOut(BaseModel):
    partner_id: str
    name: str
    type: str
    parent_org: str | None
    ifsc: str | None
    address: str | None
    district: str
    state: str
    pincode: str | None
    contact: dict[str, Any]
    lat: float | None
    lng: float | None
    is_active: bool
    authorisations: list[AuthorisationOut]
    data_disclaimer: str
