"""Console logins.

Three roles, one table. A `partner` user is scoped to exactly one Channel Partner
through `partner_id`, and every partner-side query filters on it — so the console
cannot show one partner another's queue even if a route forgets to check, because the
filter lives in the query rather than in a permission test someone can omit.

`citizen` exists as a role for completeness, but the citizen journey requires no login:
an application is tracked by its reference number alone (Phase 5). Nobody should have
to create an account to find out which scheme fits them.
"""

import uuid

from sqlalchemy import Boolean, CheckConstraint, Enum, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole
from app.models.mixins import Timestamps, UUIDPrimaryKey


class User(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    # bcrypt output. The plaintext exists only inside a request handler, never stored.
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True), nullable=False
    )

    # Set for role=PARTNER, null otherwise. The CHECK below makes that structural.
    partner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_partners.id", ondelete="CASCADE")
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    partner = relationship("ChannelPartner")

    __table_args__ = (
        # A partner login with no partner is a console showing nothing; an admin login
        # with a partner is an ambiguous scope. Neither should be representable.
        CheckConstraint(
            "(role = 'PARTNER' AND partner_id IS NOT NULL) "
            "OR (role <> 'PARTNER' AND partner_id IS NULL)",
            name="partner_role_has_a_partner",
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_partner_id", "partner_id"),
    )
