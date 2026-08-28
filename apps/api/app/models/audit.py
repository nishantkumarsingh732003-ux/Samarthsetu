"""Audit trail and the reproducibility record.

`match_runs` is the governance artefact behind "the LLM never decides eligibility":
every match writes the input snapshot, the engine version, and the full result set.
Rows here are never deleted — a decision must remain replayable after the rules change.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKey


class AuditLog(UUIDPrimaryKey, Base):
    """Who read or changed what. Append-only."""

    __tablename__ = "audit_log"

    actor: Mapped[str] = mapped_column(String(120), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    entity: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(64))
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    meta: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    __table_args__ = (
        Index("ix_audit_log_entity_entity_id", "entity", "entity_id"),
        Index("ix_audit_log_at", "at"),
        Index("ix_audit_log_actor", "actor"),
    )


class MatchRun(UUIDPrimaryKey, Base):
    """One execution of the deterministic rule engine.

    NEVER DELETE ROWS FROM THIS TABLE. It is the evidence that a given verdict was
    produced by rules, not by a language model, and it is what the admin console
    replays.
    """

    __tablename__ = "match_runs"

    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id", ondelete="SET NULL")
    )
    # The exact profile the engine saw, frozen at decision time.
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    # Full ranked MatchResult[] including matched_because / blocked_because.
    results: Mapped[list[Any]] = mapped_column(JSONB, nullable=False)
    at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_match_runs_citizen_id", "citizen_id"),
        Index("ix_match_runs_at", "at"),
        Index("ix_match_runs_engine_version", "engine_version"),
    )
