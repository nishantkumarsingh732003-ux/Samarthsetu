"""Channel Partner registry and the scheme-authorisation matrix.

The second half of the problem statement: a citizen cannot find the nearest partner
authorised for *their* loan category. `partner_scheme_authorisations` is what makes
that answerable — a partner is only routable for a scheme it has a row for.
"""

import uuid
from decimal import Decimal
from typing import Any

from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PartnerType
from app.models.mixins import Timestamps, UUIDPrimaryKey


class ChannelPartner(UUIDPrimaryKey, Timestamps, Base):
    __tablename__ = "channel_partners"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[PartnerType] = mapped_column(
        Enum(PartnerType, name="partner_type", native_enum=True), nullable=False
    )
    parent_org: Mapped[str | None] = mapped_column(String(255))
    ifsc: Mapped[str | None] = mapped_column(String(11))
    address: Mapped[str | None] = mapped_column(Text)
    district: Mapped[str] = mapped_column(String(120), nullable=False)
    state: Mapped[str] = mapped_column(String(120), nullable=False)
    pincode: Mapped[str | None] = mapped_column(String(6))
    geom: Mapped[object | None] = mapped_column(
        Geography(geometry_type="POINT", srid=4326, spatial_index=False)
    )
    # {"phone": "...", "email": "...", "contact_person": "..."}
    contact: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    authorisations: Mapped[list["PartnerSchemeAuthorisation"]] = relationship(
        back_populates="partner", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("pincode IS NULL OR pincode ~ '^[0-9]{6}$'", name="pincode_is_six_digits"),
        CheckConstraint(
            "ifsc IS NULL OR ifsc ~ '^[A-Z]{4}0[A-Z0-9]{6}$'", name="ifsc_is_well_formed"
        ),
        # PostGIS spatial index — every routing query starts with a distance sort.
        Index("ix_channel_partners_geom", "geom", postgresql_using="gist"),
        Index("ix_channel_partners_district_state", "district", "state"),
        Index("ix_channel_partners_type_active", "type", "is_active"),
    )


class PartnerSchemeAuthorisation(UUIDPrimaryKey, Timestamps, Base):
    """Which partner may process which scheme, at what ticket size, right now.

    A missing row means "not authorised" — that is the fact the routing engine reports
    back as `why_not` when a nearby partner is excluded.
    """

    __tablename__ = "partner_scheme_authorisations"

    partner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("channel_partners.id", ondelete="CASCADE"), nullable=False
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schemes.id", ondelete="CASCADE"), nullable=False
    )

    min_ticket: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    max_ticket: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    # Partner-controlled capacity switch; feeds straight back into routing (Phase 6).
    is_currently_accepting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    avg_turnaround_days: Mapped[int | None] = mapped_column(Integer)
    # Occupancy 0-100, used as a load-balancing term in the routing score.
    active_load: Mapped[int | None] = mapped_column(Integer)
    service_districts: Mapped[list[str]] = mapped_column(
        ARRAY(String(120)), nullable=False, default=list
    )

    partner: Mapped[ChannelPartner] = relationship(back_populates="authorisations")
    scheme: Mapped["Scheme"] = relationship(back_populates="authorisations")  # noqa: F821

    __table_args__ = (
        UniqueConstraint(
            "partner_id", "scheme_id", name="uq_partner_scheme_authorisations_partner_id_scheme_id"
        ),
        CheckConstraint(
            "min_ticket IS NULL OR max_ticket IS NULL OR min_ticket <= max_ticket",
            name="ticket_band_is_ordered",
        ),
        CheckConstraint(
            "active_load IS NULL OR (active_load BETWEEN 0 AND 100)",
            name="active_load_is_a_percentage",
        ),
        # GIN index so `:district = ANY(service_districts)` stays fast.
        Index(
            "ix_partner_scheme_authorisations_service_districts",
            "service_districts",
            postgresql_using="gin",
        ),
        Index(
            "ix_partner_scheme_authorisations_scheme_accepting",
            "scheme_id",
            "is_currently_accepting",
        ),
    )
