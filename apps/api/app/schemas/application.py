"""Request and response models for applications and documents.

Two shapes of note.

`ApplicantIn.gov_id` accepts the full number because a citizen will type it — but it is
masked in the route before anything is written, and the number is never echoed back.
There is no response model anywhere in this file with a field that could carry one.

`ApplicationOut` is what the tracking page renders. It is deliberately thin on personal
data: a reference number is quotable, shareable and guessable-adjacent, so it returns
the state of the application, not a dossier on the applicant.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LANGUAGES = Literal["en", "hi", "mr", "bn", "ta", "te"]


class ConsentIn(BaseModel):
    """DPDP Act 2023: an explicit, recorded grant before any citizen data is stored."""

    model_config = ConfigDict(extra="forbid")

    granted: bool = Field(
        description="Must be true. A false or absent grant is refused, not defaulted."
    )
    purpose: str = Field(
        default="scheme_eligibility_and_partner_routing",
        max_length=120,
        description="What the citizen agreed their data would be used for.",
    )


class ApplicantIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=120)
    # Masked to the last 4 before storage. Never returned.
    phone: str | None = Field(default=None, max_length=20)
    gov_id_type: Literal["AADHAAR", "PAN", "VOTER_ID", "OTHER"] | None = None
    gov_id: str | None = Field(
        default=None,
        max_length=32,
        description=(
            "Masked at ingestion. Only the last 4 digits and a salted hash are stored; "
            "the full value never reaches the database and is never echoed back."
        ),
    )
    district: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    preferred_language: LANGUAGES = "en"


class ApplicationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scheme_code: str = Field(examples=["NSFDC_MICRO_FINANCE"])
    partner_id: str | None = Field(
        default=None, description="The Channel Partner the citizen chose from routing."
    )
    amount_requested: float | None = Field(default=None, gt=0, examples=[90000])
    match_run_id: str | None = Field(
        default=None,
        description=(
            "The eligibility run this application rests on. Stored so a sanction "
            "decision can be replayed against the rules that were live at the time."
        ),
    )
    applicant: ApplicantIn = Field(default_factory=ApplicantIn)
    consent: ConsentIn
    language: LANGUAGES = "en"


class DocumentWarningOut(BaseModel):
    code: str
    message: str


class RequiredDocumentOut(BaseModel):
    id: str
    name: str
    why: str
    issued_by: str | None
    validity_months: int | None
    # True where the validity window is common partner practice rather than a published
    # rule. The UI says "most partners ask for" rather than "you must".
    validity_is_practice_not_rule: bool
    contains_government_id: bool
    # Filled in on the tracking view: has this slot been uploaded yet?
    uploaded: bool = False


class DocumentOut(BaseModel):
    id: str
    doc_type: str
    validation_status: str
    redaction_applied: bool
    warnings: list[DocumentWarningOut] = Field(default_factory=list)
    detected_type: str | None = None
    uploaded_at: str | None = None


class DocumentUploadResponse(BaseModel):
    document: DocumentOut
    # Present so a citizen sees what we read back from their own document and can tell
    # us we read it wrong. Any government ID inside is already masked.
    extract: dict[str, Any] = Field(default_factory=dict)
    masked_ids: list[dict[str, str]] = Field(default_factory=list)


class TimelineEntryOut(BaseModel):
    status: str
    actor: str
    at: str
    reason: str | None = None


class ApplicationOut(BaseModel):
    reference_no: str
    status: str
    scheme_code: str
    scheme_name: str
    family: str
    partner: dict[str, Any] | None = None
    amount_requested: float | None = None
    submitted_at: str | None = None
    engine_version: str | None = None
    match_run_id: str | None = None
    timeline: list[TimelineEntryOut] = Field(default_factory=list)
    documents: list[DocumentOut] = Field(default_factory=list)
    required_documents: list[RequiredDocumentOut] = Field(default_factory=list)
    documents_outstanding: int = 0
    checklist_needs_verification: bool = True


class ChecklistResponse(BaseModel):
    family: str
    partner_type: str | None
    language: str
    documents: list[RequiredDocumentOut]
    checklist_digest: str
    needs_verification: bool
    verification_note: str | None = None


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    to_status: Literal[
        "PARTNER_ACKNOWLEDGED",
        "DOCS_REQUESTED",
        "UNDER_APPRAISAL",
        "SANCTIONED",
        "DISBURSED",
        "REJECTED",
        "WITHDRAWN",
    ]
    reason: str | None = Field(default=None, max_length=500)
    actor: str = Field(default="partner", max_length=120)
