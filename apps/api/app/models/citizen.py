"""Citizen identity, consent, and the progressively-collected eligibility profile.

DPDP Act 2023 posture (CLAUDE.md rule 4):
- No government ID is ever stored in full. `gov_id_last4` plus a salted `gov_id_hash`
  is the maximum retained. A CHECK constraint enforces the 4-digit shape at the
  database level so a bug in application code cannot persist a full number.
- A `consents` row must exist before citizen data is stored; `citizens.consent_id` is
  NOT NULL to make that structural rather than procedural.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import Gender, GovIdType, SocialCategory
from app.models.mixins import Timestamps, UUIDPrimaryKey


class Consent(UUIDPrimaryKey, Base):
    """An explicit, revocable grant recorded before any citizen data is stored."""

    __tablename__ = "consents"

    purpose: Mapped[str] = mapped_column(String(120), nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Salted hash, never the raw address.
    ip_hash: Mapped[str | None] = mapped_column(String(64))

    citizens: Mapped[list["Citizen"]] = relationship(back_populates="consent")

    __table_args__ = (Index("ix_consents_granted_at", "granted_at"),)


class Citizen(UUIDPrimaryKey, Timestamps, Base):
    """A citizen, identified only by masked credentials."""

    __tablename__ = "citizens"

    gov_id_type: Mapped[GovIdType | None] = mapped_column(
        Enum(GovIdType, name="gov_id_type", native_enum=True)
    )
    gov_id_last4: Mapped[str | None] = mapped_column(String(4))
    # sha256(salt || full_id) — lets us de-duplicate without ever holding the number.
    gov_id_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    phone_last4: Mapped[str | None] = mapped_column(String(4))

    consent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("consents.id", ondelete="RESTRICT"), nullable=False
    )

    preferred_language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    district: Mapped[str | None] = mapped_column(String(120))
    state: Mapped[str | None] = mapped_column(String(120))
    # Free text, and deliberately not validated against a gazetteer: a citizen who
    # writes their village rather than the block headquarters is still findable, and
    # routing uses `district` and `geom`, never this.
    city: Mapped[str | None] = mapped_column(String(120))
    pincode: Mapped[str | None] = mapped_column(String(6))
    geom: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )

    consent: Mapped[Consent] = relationship(back_populates="citizens")
    profile: Mapped["CitizenProfile | None"] = relationship(
        back_populates="citizen", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "gov_id_last4 IS NULL OR gov_id_last4 ~ '^[0-9]{4}$'",
            name="gov_id_last4_is_four_digits",
        ),
        CheckConstraint(
            "phone_last4 IS NULL OR phone_last4 ~ '^[0-9]{4}$'",
            name="phone_last4_is_four_digits",
        ),
        CheckConstraint(
            "pincode IS NULL OR pincode ~ '^[1-9][0-9]{5}$'",
            name="pincode_is_six_digits",
        ),
        Index("ix_citizens_district_state", "district", "state"),
        Index("ix_citizens_geom", "geom", postgresql_using="gist"),
    )


class CitizenProfile(UUIDPrimaryKey, Timestamps, Base):
    """Eligibility facts.

    Every field is nullable on purpose: the conversational intake collects them
    progressively, and the rule engine reports NEED_MORE_INFO for a hard-block rule
    that references a field still NULL (CLAUDE.md / Phase 1).
    """

    __tablename__ = "citizen_profiles"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("citizens.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    annual_family_income: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    category: Mapped[SocialCategory | None] = mapped_column(
        Enum(SocialCategory, name="social_category", native_enum=True)
    )
    sub_category: Mapped[str | None] = mapped_column(String(120))
    gender: Mapped[Gender | None] = mapped_column(Enum(Gender, name="gender", native_enum=True))
    age: Mapped[int | None] = mapped_column(SmallInteger)
    occupation_type: Mapped[str | None] = mapped_column(String(120))
    education_level: Mapped[str | None] = mapped_column(String(120))
    # Total outstanding borrowing across existing loans, in rupees.
    existing_loans: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    project_cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    project_sector: Mapped[str | None] = mapped_column(String(120))
    is_pwd: Mapped[bool | None] = mapped_column(Boolean)
    is_safai_karamchari: Mapped[bool | None] = mapped_column(Boolean)
    has_caste_certificate: Mapped[bool | None] = mapped_column(Boolean)
    admission_confirmed: Mapped[bool | None] = mapped_column(Boolean)
    course_start_date: Mapped[object | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)

    # --- collected by the onboarding, not read by the rule engine ------------------
    # The engine's contract is `setu_rules.profile.FIELDS` and nothing below appears in
    # it. These columns exist so a signed-in citizen does not retype their enterprise
    # every visit, and so a partner opening the application sees what it is for. A rule
    # that wants one of them has to add it to the engine contract first, deliberately.
    business_name: Mapped[str | None] = mapped_column(String(160))
    business_description: Mapped[str | None] = mapped_column(Text)
    # NEW for a unit not yet trading, EXISTING for one that is. Which of the two you
    # are changes whether a partner asks for trading proof, so it is worth storing.
    business_status: Mapped[str | None] = mapped_column(String(16))
    own_contribution: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    loan_required: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # Set when the citizen finishes onboarding. Null means "still filling it in", which
    # is a different thing from "every field happens to be empty".
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    citizen: Mapped[Citizen] = relationship(back_populates="profile")

    __table_args__ = (
        CheckConstraint("annual_family_income IS NULL OR annual_family_income >= 0",
                        name="annual_family_income_non_negative"),
        CheckConstraint("project_cost IS NULL OR project_cost >= 0",
                        name="project_cost_non_negative"),
        CheckConstraint("age IS NULL OR (age BETWEEN 0 AND 120)", name="age_within_range"),
        CheckConstraint(
            "own_contribution IS NULL OR own_contribution >= 0",
            name="own_contribution_non_negative",
        ),
        CheckConstraint(
            "loan_required IS NULL OR loan_required >= 0", name="loan_required_non_negative"
        ),
        # The share a citizen brings cannot exceed the project it is brought to. The
        # *upper* bound on what may be borrowed is a scheme rule with provenance
        # (`max_funding_pct`), not a number hardcoded here.
        CheckConstraint(
            "own_contribution IS NULL OR project_cost IS NULL "
            "OR own_contribution <= project_cost",
            name="own_contribution_within_project_cost",
        ),
        CheckConstraint(
            "business_status IS NULL OR business_status IN ('NEW', 'EXISTING')",
            name="business_status_is_known",
        ),
    )
