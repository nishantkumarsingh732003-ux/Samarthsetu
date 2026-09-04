"""Console logins.

Three roles, one table. A `partner` user is scoped to exactly one Channel Partner
through `partner_id`, and every partner-side query filters on it — so the console
cannot show one partner another's queue even if a route forgets to check, because the
filter lives in the query rather than in a permission test someone can omit.

A `citizen` user is optional, and that is the whole point. The anonymous journey still
works end to end — an application is tracked by its reference number alone (Phase 5),
and nobody has to create an account to find out which scheme fits them. Signing in only
adds persistence: a profile that survives the walk home, and a list of your own
applications instead of a reference number on a scrap of paper. `citizen_id` is the link
to that stored profile, and it is NULL for the two console roles.
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

    # Set for role=CITIZEN, null otherwise. The citizen row carries the consent record
    # and the eligibility profile; this column is only the link from a login to it.
    citizen_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("citizens.id", ondelete="RESTRICT"), unique=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    partner = relationship("ChannelPartner")
    citizen = relationship("Citizen")

    __table_args__ = (
        # A partner login with no partner is a console showing nothing; an admin login
        # with a partner is an ambiguous scope. Neither should be representable.
        CheckConstraint(
            "(role = 'PARTNER' AND partner_id IS NOT NULL) "
            "OR (role <> 'PARTNER' AND partner_id IS NULL)",
            name="partner_role_has_a_partner",
        ),
        # A console login pointing at a citizen profile is an ambiguous scope in the
        # other direction. Only a CITIZEN may carry one; the role does not have to.
        CheckConstraint(
            "citizen_id IS NULL OR role = 'CITIZEN'",
            name="only_a_citizen_role_has_a_citizen",
        ),
        Index("ix_users_role", "role"),
        Index("ix_users_partner_id", "partner_id"),
    )
