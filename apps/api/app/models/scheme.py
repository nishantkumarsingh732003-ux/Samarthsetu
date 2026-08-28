"""Scheme catalogue and the versioned rules attached to each scheme.

CLAUDE.md rule 2: every rule carries provenance. `source_url`, `circular_ref`,
`effective_from`, and `last_verified_on` are therefore columns, not comments, and
`needs_verification` marks any figure the problem statement does not actually state.
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RuleSeverity, SchemeFamily
from app.models.mixins import Timestamps, UUIDPrimaryKey

# intfloat/multilingual-e5-base output dimensionality.
EMBEDDING_DIM = 768


class Scheme(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "schemes"

    code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    # Official name is kept verbatim and never machine-translated (CLAUDE.md).
    official_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Transliterated glosses per locale: {"hi": "...", "ta": "..."}.
    name_i18n: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    family: Mapped[SchemeFamily] = mapped_column(
        Enum(SchemeFamily, name="scheme_family", native_enum=True), nullable=False
    )

    max_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    max_funding_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    interest_rate_min: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    interest_rate_max: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    tenure_months: Mapped[int | None] = mapped_column(Integer)
    moratorium_months: Mapped[int | None] = mapped_column(Integer)

    # --- provenance (CLAUDE.md rule 2) ---
    source_url: Mapped[str | None] = mapped_column(Text)
    circular_ref: Mapped[str | None] = mapped_column(String(255))
    effective_from: Mapped[date | None] = mapped_column(Date)
    last_verified_on: Mapped[date | None] = mapped_column(Date)
    # True when one or more figures above are not stated in an official source yet.
    needs_verification: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # pgvector column for semantic scheme search over the description corpus.
    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBEDDING_DIM))

    rules: Mapped[list["SchemeRule"]] = relationship(
        back_populates="scheme", cascade="all, delete-orphan"
    )
    authorisations: Mapped[list["PartnerSchemeAuthorisation"]] = relationship(  # noqa: F821
        back_populates="scheme", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "max_funding_pct IS NULL OR (max_funding_pct > 0 AND max_funding_pct <= 100)",
            name="max_funding_pct_is_a_percentage",
        ),
        CheckConstraint(
            "interest_rate_min IS NULL OR interest_rate_max IS NULL "
            "OR interest_rate_min <= interest_rate_max",
            name="interest_band_is_ordered",
        ),
        Index("ix_schemes_family_active", "family", "is_active"),
    )


class SchemeRule(UUIDPrimaryKey, Timestamps, Base):
    """One eligibility rule.

    `expression` is the JSON form of the YAML rule DSL authored in
    `packages/rules/schemes/*.yaml` (Phase 1). It is data, never code: policy changes
    are a YAML edit plus an `engine_version` bump, not a deployment.
    """

    __tablename__ = "scheme_rules"

    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )
    # Stable, human-quotable identifier, e.g. "MF_INCOME_CEILING".
    rule_id: Mapped[str] = mapped_column(String(64), nullable=False)
    expression: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    severity: Mapped[RuleSeverity] = mapped_column(
        Enum(RuleSeverity, name="rule_severity", native_enum=True), nullable=False
    )
    message_i18n: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    # The anti-misrouting feature: which scheme code to offer when this rule blocks.
    suggest_instead: Mapped[str | None] = mapped_column(String(64))

    scheme: Mapped[Scheme] = relationship(back_populates="rules")

    __table_args__ = (
        UniqueConstraint("scheme_id", "rule_id", name="uq_scheme_rules_scheme_id_rule_id"),
        Index("ix_scheme_rules_severity", "severity"),
    )
