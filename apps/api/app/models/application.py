"""Applications and their supporting documents.

An application snapshots the `match_run` and `engine_version` that produced it, so a
sanction decision can always be replayed against the exact rules that were live when
the citizen applied — even after the YAML changes.
"""

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import ApplicationStatus, DocumentValidationStatus
from app.models.mixins import Timestamps, UUIDPrimaryKey


class Application(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "applications"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id", ondelete="RESTRICT"), nullable=False
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="RESTRICT"), nullable=False
    )
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_partners.id", ondelete="RESTRICT")
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status", native_enum=True),
        nullable=False,
        default=ApplicationStatus.DRAFT,
    )
    amount_requested: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    # Human-readable and quotable at a branch counter, e.g. SETU-2026-MH-000431.
    reference_no: Mapped[str] = mapped_column(String(32), nullable=False, unique=True)

    # Reproducibility: which decision, under which engine, produced this application.
    match_run_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("match_runs.id", ondelete="SET NULL")
    )
    engine_version: Mapped[str | None] = mapped_column(String(32))

    # Append-only list of {status, actor, at, reason}.
    status_history: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    documents: Mapped[list["Document"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "amount_requested IS NULL OR amount_requested > 0",
            name="amount_requested_is_positive",
        ),
        Index("ix_applications_status", "status"),
        Index("ix_applications_partner_status", "partner_id", "status"),
        Index("ix_applications_citizen_id", "citizen_id"),
    )


class Document(UUIDPrimaryKey, Timestamps, Base):
    """An uploaded supporting document plus its OCR pre-validation result."""

    __tablename__ = "documents"

    application_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    doc_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_key: Mapped[str] = mapped_column(Text, nullable=False)
    # Extracted fields only. Any government ID inside is already masked to last 4.
    ocr_extract: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    validation_status: Mapped[DocumentValidationStatus] = mapped_column(
        Enum(DocumentValidationStatus, name="document_validation_status", native_enum=True),
        nullable=False,
        default=DocumentValidationStatus.PENDING,
    )
    # True once the stored image itself has the ID region painted over (Phase 5).
    redaction_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    application: Mapped[Application] = relationship(back_populates="documents")

    __table_args__ = (
        Index("ix_documents_application_id", "application_id"),
        Index("ix_documents_validation_status", "validation_status"),
    )
