"""Request and response models for optional citizen accounts.

The shapes here are the seam between a form and the rule engine, and they are
deliberately stricter than the form. `extra="forbid"` everywhere means a client that
invents a field gets a 422 naming it, rather than having the answer silently dropped
and then wondering why the verdict did not move.

Nothing in this module carries a government ID. Signup collects an email, a password and
a name; the ID masking in `services/citizens.py` stays the only path by which an ID ever
enters the system, and it enters masked.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.match import LANGUAGES, MatchResultOut, NextQuestionOut

# bcrypt hashes at most 72 bytes, and `security.hash_password` refuses more rather than
# truncating. Capping here turns that into a field error on the form instead of a 500.
MAX_PASSWORD_LENGTH = 72
MIN_PASSWORD_LENGTH = 8


class SignupRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255, examples=["rahul@example.com"])
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=MAX_PASSWORD_LENGTH)
    display_name: str = Field(min_length=1, max_length=120, examples=["Rahul Kumar"])
    preferred_language: LANGUAGES = "en"
    # An account stores personal data, so it cannot be created without an explicit
    # grant. This is not a checkbox for show: `create_account` writes the `consents` row
    # this represents before it writes the citizen, and the database will not accept a
    # citizen without one.
    consent: bool = Field(
        description="Explicit consent to store the profile against this account (DPDP)."
    )


class CitizenProfileIn(BaseModel):
    """A partial profile update. Every field is optional and absent means 'leave it'.

    An explicit `null` clears a field; omitting the key does not. On a 2G connection a
    half-submitted form is normal, and it must not erase last week's answers.
    """

    model_config = ConfigDict(extra="forbid")

    # --- identity and location (stored on `citizens`) ---
    display_name: str | None = Field(default=None, max_length=120)
    preferred_language: LANGUAGES | None = None
    district: str | None = Field(default=None, max_length=120)
    state: str | None = Field(default=None, max_length=120)
    city: str | None = Field(default=None, max_length=120)
    pincode: str | None = Field(default=None, pattern=r"^[1-9][0-9]{5}$")

    # --- read by the rule engine ---
    category: Literal["SC", "ST", "OBC", "GENERAL"] | None = None
    sub_category: str | None = Field(default=None, max_length=120)
    gender: Literal["FEMALE", "MALE", "OTHER", "UNDISCLOSED"] | None = None
    age: int | None = Field(default=None, ge=0, le=120)
    annual_family_income: float | None = Field(default=None, ge=0)
    occupation_type: str | None = Field(default=None, max_length=120)
    education_level: str | None = Field(default=None, max_length=120)
    existing_loans: float | None = Field(default=None, ge=0)
    project_cost: float | None = Field(default=None, ge=0)
    project_sector: (
        Literal[
            "AGRICULTURE",
            "MANUFACTURING",
            "SERVICES",
            "TRADE",
            "TRANSPORT",
            "ARTISAN",
            "EDUCATION",
            "OTHER",
        ]
        | None
    ) = None
    is_pwd: bool | None = None
    is_safai_karamchari: bool | None = None
    has_caste_certificate: bool | None = None
    admission_confirmed: bool | None = None
    course_start_date: date | None = None

    # --- collected by onboarding, never read by the engine ---
    business_name: str | None = Field(default=None, max_length=160)
    business_description: str | None = Field(default=None, max_length=2000)
    business_status: Literal["NEW", "EXISTING"] | None = None
    own_contribution: float | None = Field(default=None, ge=0)
    loan_required: float | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)

    # Marks onboarding finished. Sending `false` reopens it.
    completed: bool | None = None

    def patch(self) -> dict[str, Any]:
        """Only the keys the caller actually sent, with `completed` split off."""
        return self.model_dump(exclude_unset=True, exclude={"completed"})


class CitizenProfileOut(BaseModel):
    """The profile as the citizen sees it, plus what the engine would be given.

    `engine_profile` is exposed on purpose. It is the exact dictionary handed to the
    deterministic rule engine, so a citizen — or a judge — can see that the enterprise
    description and the business name are not among the things deciding the verdict.
    """

    display_name: str | None
    preferred_language: str
    district: str | None
    state: str | None
    city: str | None
    pincode: str | None

    category: str | None
    sub_category: str | None
    gender: str | None
    age: int | None
    annual_family_income: float | None
    occupation_type: str | None
    education_level: str | None
    existing_loans: float | None
    project_cost: float | None
    project_sector: str | None
    is_pwd: bool | None
    is_safai_karamchari: bool | None
    has_caste_certificate: bool | None
    admission_confirmed: bool | None
    course_start_date: date | None

    business_name: str | None
    business_description: str | None
    business_status: str | None
    own_contribution: float | None
    loan_required: float | None

    completed: bool
    completion_pct: int
    engine_profile: dict[str, Any]


class CitizenAccountOut(BaseModel):
    """Who is signed in, and the profile behind them."""

    id: str
    email: str
    display_name: str
    role: str
    citizen_id: str
    profile: CitizenProfileOut


class SignupResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in_minutes: int
    user: CitizenAccountOut


class CitizenMatchResponse(BaseModel):
    """The stored profile, run through the same deterministic engine as everyone else.

    Identical in shape to `POST /match` because it *is* the same call — the only
    difference is where the profile came from. A signed-in citizen gets no different
    verdict from an anonymous one with the same facts, and this shared shape is how that
    stays true.
    """

    match_run_id: str
    engine_version: str
    rules_digest: str
    input_snapshot: dict[str, Any]
    results: list[MatchResultOut]
    next_question: NextQuestionOut | None
    # False when the profile is too empty to decide anything yet, so the UI can send the
    # citizen to onboarding instead of showing an empty results page.
    profile_is_usable: bool


class CitizenApplicationSummary(BaseModel):
    """One row in 'my applications'. The detail view is the existing tracking endpoint."""

    reference_no: str
    status: str
    scheme_code: str
    scheme_name: str
    family: str
    partner_name: str | None
    amount_requested: float | None
    submitted_at: str | None
    documents_outstanding: int


class CitizenNotificationOut(BaseModel):
    """One message this service sent to the signed-in citizen, as it was sent.

    The body is stored already rendered, in the language it went out in, so what a
    citizen reads here is the message itself and not a re-render of a template that may
    have been rewritten since. That is the whole point of keeping the row: someone who
    says "nobody told me" can be shown exactly what was sent and when.

    **There is no contact address on this shape, and there must never be one.** The row
    carries `recipient_hint` — the four masked digits an officer uses in the console to
    confirm they have the right person — and it is deliberately not projected here. A
    citizen reading their own feed does not need to be told their own number, and a field
    that is never returned is a field that cannot leak. `test_security_surface.py`
    asserts it.
    """

    id: str
    # The trigger, e.g. APPLICATION_SUBMITTED. Stable across template rewrites, which is
    # what lets the UI pick an icon without parsing the body.
    event: str
    channel: str
    language: str
    body: str
    status: str
    # Null while a message is queued or has failed. The row still exists, and a citizen
    # is entitled to see that we tried.
    sent_at: str | None
    created_at: str
    application_reference: str | None
