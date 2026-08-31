"""Outbound messages to a citizen.

One row per message, rendered at send time in the citizen's own language and kept —
so a citizen who says "nobody told me" can be shown exactly what was sent, when, and
through which channel. That record is the point; the delivery channel is swappable.

**There is no phone number here.** Phase 5 stores `phone_last4` only, and this table
does not reintroduce a dialable address by the back door: `recipient_hint` is the same
masked four digits, for display in the console. A driver that needs a real number says
so and fails; see `services/notifications.py` and OPEN_ITEMS OI-43.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import NotificationChannel, NotificationStatus
from app.models.mixins import Timestamps, UUIDPrimaryKey


class Notification(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "notifications"

    citizen_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id", ondelete="CASCADE"), nullable=False
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE")
    )

    # The trigger, e.g. APPLICATION_SUBMITTED. Stable across template rewrites.
    event: Mapped[str] = mapped_column(String(64), nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel, name="notification_channel", native_enum=True), nullable=False
    )
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")

    # Rendered at send time, in the citizen's language, and kept verbatim.
    body: Mapped[str] = mapped_column(Text, nullable=False)
    # What the template was filled with. Never contains a government ID.
    context: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    # Last four digits only — enough for an officer to confirm the right person, and
    # not enough to dial.
    recipient_hint: Mapped[str | None] = mapped_column(String(4))

    status: Mapped[NotificationStatus] = mapped_column(
        Enum(NotificationStatus, name="notification_status", native_enum=True),
        nullable=False,
        default=NotificationStatus.PENDING,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Why a send failed, in the operator's words. Shown in the console, never to the
    # citizen — "no contact channel on file" is our problem, not theirs.
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # SMS billing is per segment, and a Tamil message costs 70 characters a segment
    # against 160 for plain Latin. Recorded so the cost of translating well is visible.
    sms_segments: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_notifications_citizen_id", "citizen_id"),
        Index("ix_notifications_application_id", "application_id"),
        Index("ix_notifications_status", "status"),
        Index("ix_notifications_event", "event"),
    )
