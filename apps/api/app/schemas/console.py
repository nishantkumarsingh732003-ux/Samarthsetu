"""Request and response models for the partner console and the MoSJE dashboard.

The queue models are where the privacy posture becomes visible. A Channel Partner
processing a loan legitimately needs to know who the applicant is — but SETU never held
the full Aadhaar to begin with, so the console shows a name, a masked ID and the last
four digits of a phone number, and the real KYC happens at the branch with the document
in hand. That is not a limitation we worked around; it is the design.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: str = Field(max_length=255, examples=["partner@setu.gov.in"])
    password: str = Field(max_length=128)


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    partner_id: str | None = None
    partner_name: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_minutes: int
    user: UserOut


class ApplicantSummary(BaseModel):
    """Everything the console may show about a citizen, and nothing more."""

    display_name: str | None = None
    # Last four digits only. The full number was never stored (CLAUDE.md rule 4).
    gov_id_type: str | None = None
    gov_id_last4: str | None = None
    phone_last4: str | None = None
    district: str | None = None
    state: str | None = None
    preferred_language: str = "en"


class ReadinessOut(BaseModel):
    """How close this application is to being processable, and what is missing."""

    score: float = Field(ge=0, le=1)
    uploaded: int
    required: int
    missing: list[str]
    warnings: int
    # True where a stored document could not have its ID masked automatically.
    unmasked_documents: int = 0


class QueueItem(BaseModel):
    reference_no: str
    status: str
    scheme_code: str
    scheme_name: str
    family: str
    amount_requested: float | None
    submitted_at: str | None
    days_open: int
    # Against the partner's own avg_turnaround_days for this scheme.
    sla_days: int | None
    sla_state: Literal["ON_TRACK", "DUE", "BREACHED", "UNKNOWN"]
    applicant: ApplicantSummary
    readiness: ReadinessOut
    # Why the router sent this application here, carried from the routing decision.
    verdict: str | None = None
    matched_because: list[dict[str, Any]] = Field(default_factory=list)
    engine_version: str | None = None


class QueueResponse(BaseModel):
    partner_id: str
    partner_name: str
    is_currently_accepting: bool
    total: int
    items: list[QueueItem]
    counts_by_status: dict[str, int]


class PartnerActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["ACKNOWLEDGE", "REQUEST_DOCS", "APPRAISE", "SANCTION", "DISBURSE", "REJECT"]
    reason: str | None = Field(default=None, max_length=500)


class CapacityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_code: str | None = Field(
        default=None,
        description="Limit the change to one scheme. Omit to apply to every authorisation.",
    )
    is_currently_accepting: bool | None = None
    max_ticket: float | None = Field(default=None, gt=0)


class CapacityRow(BaseModel):
    scheme_code: str
    scheme_name: str
    family: str
    is_currently_accepting: bool
    min_ticket: float | None
    max_ticket: float | None
    avg_turnaround_days: int | None
    active_load: int | None


class CapacityResponse(BaseModel):
    partner_id: str
    partner_name: str
    rows: list[CapacityRow]


# --- analytics -----------------------------------------------------------------------


class FunnelStage(BaseModel):
    stage: str
    label: str
    count: int
    # Share of the stage before it. None for the first stage.
    conversion_from_previous: float | None = None


class FunnelOut(BaseModel):
    stages: list[FunnelStage]
    largest_drop_off: str | None
    largest_drop_off_pct: float | None


class MisroutingOut(BaseModel):
    """The primary KPI: applications that would have gone to the wrong counter."""

    redirects_suggested: int
    partners_filtered_for_authorisation: int
    partners_filtered_for_distance: int
    partners_filtered_for_ticket_size: int
    routing_calls: int
    total_prevented: int


class UnderservedDistrict(BaseModel):
    district: str
    state: str
    demand: int
    partners_within_25km: int
    nearest_authorised_km: float | None
    families_unserved: list[str]


class CoverageOut(BaseModel):
    radius_km: float
    districts_with_demand: int
    underserved: list[UnderservedDistrict]
    # Rendered as a bubble map rather than a choropleth; see the note in the README.
    points: list[dict[str, Any]]


class BreakdownRow(BaseModel):
    key: str
    label: str
    count: int
    share: float


class TurnaroundRow(BaseModel):
    partner_type: str
    applications: int
    median_days: float | None
    p90_days: float | None


class AnalyticsOut(BaseModel):
    generated_at: str
    engine_version: str
    funnel: FunnelOut
    misrouting: MisroutingOut
    coverage: CoverageOut
    scheme_mix: list[BreakdownRow]
    language_mix: list[BreakdownRow]
    turnaround: list[TurnaroundRow]
    status_mix: list[BreakdownRow]
