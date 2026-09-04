"""Public read-only surfaces: the scheme catalogue and partner coverage.

Both are unauthenticated on purpose. Which schemes exist, what they are worth, where the
numbers came from and which Channel Partners are authorised where — none of that is
personal data, and requiring a login to read published government terms would be the
opposite of the transparency this project is named for.

Every scheme carries its provenance block, including the questions still open against
it. A figure this project could not source is labelled as such rather than quietly
rounded into confidence.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class OpenQuestionOut(BaseModel):
    """A figure we could not source, named rather than guessed."""

    field: str
    question: str


class ProvenanceOut(BaseModel):
    source: str | None
    source_url: str | None
    circular_ref: str | None
    effective_from: str | None
    last_verified_on: str | None
    needs_verification: bool
    verification_note: str | None
    open_questions: list[OpenQuestionOut]


class LimitsOut(BaseModel):
    """The published terms. Every one of these is sourced in the provenance block."""

    min_project_cost: float | None
    max_project_cost: float | None
    max_loan_amount: float | None
    max_funding_pct: float | None
    interest_rate_min: float | None
    interest_rate_max: float | None
    tenure_months: int | None
    moratorium_months: int | None


class SchemeRuleOut(BaseModel):
    """One eligibility rule, in the words a citizen reads and the form the engine runs.

    `when_source` is the rule DSL expression verbatim. Publishing it is the point: a
    verdict that cites `MF_INCOME_CEILING` can be checked against the expression that
    carries that id, by anyone, without access to the database.
    """

    rule_id: str
    severity: str
    when_source: str
    message: str
    satisfied_message: str | None
    suggest_instead: str | None
    fields: list[str]


class SchemeSummaryOut(BaseModel):
    code: str
    # Official names are kept verbatim and never machine-translated (CLAUDE.md).
    official_name: str
    name_gloss: str | None = Field(
        default=None, description="Transliterated gloss in the requested language."
    )
    family: str
    limits: LimitsOut
    provenance: ProvenanceOut
    rule_count: int
    hard_block_count: int
    # How many Channel Partners are authorised for this scheme and currently accepting.
    authorised_partner_count: int
    translation_status: str


class SchemeDetailOut(SchemeSummaryOut):
    rules: list[SchemeRuleOut]
    required_documents: list[dict[str, Any]]
    checklist_digest: str


class SchemeCatalogueOut(BaseModel):
    engine_version: str
    rules_digest: str
    language: str
    schemes: list[SchemeSummaryOut]


# --- partner coverage -------------------------------------------------------------------


class DistrictCoverageOut(BaseModel):
    district: str
    state: str
    partner_count: int
    # Partner counts by type, e.g. {"SCA": 2, "PSB": 5}. The mix matters: a district with
    # five banks and no State Channelising Agency routes differently from one with both.
    by_type: dict[str, int]
    scheme_codes: list[str]


class StateCoverageOut(BaseModel):
    state: str
    partner_count: int
    district_count: int
    by_type: dict[str, int]
    scheme_codes: list[str]


class CoverageOut(BaseModel):
    """Where the Channel Finance System actually reaches.

    A blank district is a real finding, not a rendering bug — it is the misrouting this
    project exists to prevent, visible before a citizen walks into the wrong branch.
    """

    states: list[StateCoverageOut]
    total_partners: int
    data_disclaimer: str


class StateDrilldownOut(BaseModel):
    state: str
    districts: list[DistrictCoverageOut]
    total_partners: int
    data_disclaimer: str


class PartnerListItemOut(BaseModel):
    """A directory row. Routing — which partner a citizen should actually go to — is
    `POST /partners/route`, which scores on distance, ticket size and load. This is the
    flat list behind a map, and it is deliberately not ranked."""

    partner_id: str
    name: str
    type: str
    parent_org: str | None
    district: str
    state: str
    pincode: str | None
    address: str | None
    contact: dict[str, Any]
    lat: float | None
    lng: float | None
    scheme_codes: list[str]
    is_accepting: bool


class PartnerListOut(BaseModel):
    partners: list[PartnerListItemOut]
    total: int
    truncated: bool
    data_disclaimer: str
