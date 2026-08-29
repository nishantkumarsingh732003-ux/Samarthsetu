"""Geo-aware Channel Partner routing.

This is the second half of the problem statement. A citizen who has been told which
scheme fits still cannot act until they know which nearby partner is *authorised* to
process that specific scheme. Getting that wrong is the misrouting the whole project
exists to prevent, so the service is built to be explicit about two things:

  1. Why the partners it returns are ranked the way they are — every score component
     is returned separately, never as a single opaque number.
  2. Why the partners it excluded were excluded — `why_not` names the nearest
     rejected branches and the exact rule that ruled each one out.

A missing `partner_scheme_authorisations` row is not an absence of data. It means "not
authorised", and that is reportable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.routing_config import (
    CANDIDATE_LIMIT,
    FASTEST_TURNAROUND_DAYS,
    MAX_SERVICE_RADIUS_KM,
    MAX_USEFUL_DISTANCE_KM,
    ROUTING_VERSION,
    SLOWEST_TURNAROUND_DAYS,
    TOP_N_RESULTS,
    TOP_N_WHY_NOT,
    TYPE_AFFINITY,
    WEIGHTS,
)
from app.models import ChannelPartner, PartnerSchemeAuthorisation, Scheme

SYNTHETIC_DISCLAIMER = (
    "Channel Partner records are synthetic demo data pending the official MoSJE "
    "partner master. Branch locations, capacity and contact details are invented."
)


class SchemeNotFound(LookupError):
    pass


class OriginUnknown(ValueError):
    """Neither coordinates nor a district we can locate were supplied."""


@dataclass(slots=True)
class Rejection:
    partner_id: str
    name: str
    type: str
    district: str
    distance_km: float | None
    reason_code: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner_id": self.partner_id,
            "name": self.name,
            "type": self.type,
            "district": self.district,
            "distance_km": self.distance_km,
            "reason_code": self.reason_code,
            "reason": self.reason,
        }


@dataclass(slots=True)
class RoutedPartner:
    partner_id: str
    name: str
    type: str
    parent_org: str | None
    ifsc: str | None
    address: str | None
    district: str
    state: str
    pincode: str | None
    contact: dict[str, Any]
    # The citizen-facing map needs to place this branch, not just say how far it is.
    lat: float | None
    lng: float | None
    distance_km: float | None
    avg_turnaround_days: int | None
    active_load: int | None
    min_ticket: float | None
    max_ticket: float | None
    score: float
    score_breakdown: dict[str, dict[str, Any]] = field(default_factory=dict)
    rank: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "partner_id": self.partner_id,
            "name": self.name,
            "type": self.type,
            "parent_org": self.parent_org,
            "ifsc": self.ifsc,
            "address": self.address,
            "district": self.district,
            "state": self.state,
            "pincode": self.pincode,
            "contact": self.contact,
            "lat": self.lat,
            "lng": self.lng,
            "distance_km": self.distance_km,
            "avg_turnaround_days": self.avg_turnaround_days,
            "active_load": self.active_load,
            "min_ticket": self.min_ticket,
            "max_ticket": self.max_ticket,
            "score": self.score,
            "score_breakdown": self.score_breakdown,
            "rank": self.rank,
        }


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _distance_score(distance_km: float | None) -> float:
    if distance_km is None:
        return 0.5  # unknown location: neutral, never a bonus or a penalty
    return _clamp(1.0 - distance_km / MAX_USEFUL_DISTANCE_KM)


def _turnaround_score(days: int | None) -> float:
    if days is None:
        return 0.5
    span = SLOWEST_TURNAROUND_DAYS - FASTEST_TURNAROUND_DAYS
    return _clamp(1.0 - (days - FASTEST_TURNAROUND_DAYS) / span)


def _load_score(active_load: int | None) -> float:
    if active_load is None:
        return 0.5
    return _clamp(1.0 - active_load / 100.0)


def _affinity_score(family: Any, partner_type: Any) -> float:
    return TYPE_AFFINITY.get(family, {}).get(partner_type, 0.5)


async def _resolve_origin(
    session: AsyncSession, lat: float | None, lng: float | None, district: str | None
) -> tuple[float, float] | None:
    """Use the caller's coordinates, else the centre of the named district.

    Deriving the district centre from the partners already in it avoids shipping a
    second copy of the geography and stays correct as the registry grows.
    """
    if lat is not None and lng is not None:
        return lat, lng
    if not district:
        return None

    # geom is GEOGRAPHY; ST_X/ST_Y need GEOMETRY, hence the cast.
    as_geometry = cast(ChannelPartner.geom, Geometry)
    centre = (
        await session.execute(
            select(func.avg(func.ST_Y(as_geometry)), func.avg(func.ST_X(as_geometry)))
            .where(func.lower(ChannelPartner.district) == func.lower(district))
        )
    ).first()

    if centre is None or centre[0] is None:
        return None
    return float(centre[0]), float(centre[1])


async def find_partners(
    session: AsyncSession,
    scheme_code: str,
    amount: float,
    lat: float | None = None,
    lng: float | None = None,
    district: str | None = None,
) -> dict[str, Any]:
    """Rank the partners that can actually process this scheme for this citizen."""
    scheme = (
        await session.execute(select(Scheme).where(Scheme.code == scheme_code))
    ).scalar_one_or_none()
    if scheme is None:
        raise SchemeNotFound(scheme_code)

    origin = await _resolve_origin(session, lat, lng, district)
    if origin is None and district:
        raise OriginUnknown(
            f"No coordinates supplied and no partners on record in district {district!r}."
        )

    # One pass over the nearest partners, LEFT JOINed to their authorisation for THIS
    # scheme. The outer join is deliberate: a NULL authorisation is the single most
    # important fact the `why_not` list reports.
    auth = PartnerSchemeAuthorisation
    distance_expr = (
        func.ST_Distance(
            ChannelPartner.geom,
            func.ST_GeogFromText(f"SRID=4326;POINT({origin[1]} {origin[0]})"),
        )
        if origin
        else None
    )

    # geom is GEOGRAPHY; ST_X/ST_Y need GEOMETRY.
    as_geometry = cast(ChannelPartner.geom, Geometry)
    columns = [ChannelPartner, auth, func.ST_Y(as_geometry), func.ST_X(as_geometry)]
    if distance_expr is not None:
        columns.append(distance_expr.label("distance_m"))

    stmt = (
        select(*columns)
        .outerjoin(
            auth, and_(auth.partner_id == ChannelPartner.id, auth.scheme_id == scheme.id)
        )
        .where(ChannelPartner.is_active.is_(True))
    )
    if distance_expr is not None:
        stmt = stmt.order_by(distance_expr)
    else:
        stmt = stmt.order_by(ChannelPartner.name)
    stmt = stmt.limit(CANDIDATE_LIMIT)

    rows = (await session.execute(stmt)).all()

    accepted: list[RoutedPartner] = []
    rejected: list[Rejection] = []

    for row in rows:
        partner: ChannelPartner = row[0]
        authorisation: PartnerSchemeAuthorisation | None = row[1]
        lat = float(row[2]) if row[2] is not None else None
        lng = float(row[3]) if row[3] is not None else None
        distance_km = round(row[4] / 1000.0, 2) if distance_expr is not None else None

        rejection = _reject_reason(partner, authorisation, scheme, amount, district, distance_km)
        if rejection is not None:
            rejected.append(rejection)
            continue

        accepted.append(_score(partner, authorisation, scheme, distance_km, lat, lng))

    accepted.sort(key=lambda p: (-p.score, p.distance_km or 0.0, p.name))
    top = accepted[:TOP_N_RESULTS]
    for i, p in enumerate(top, start=1):
        p.rank = i

    return {
        "routing_version": ROUTING_VERSION,
        "scheme_code": scheme.code,
        "scheme_name": scheme.official_name,
        "amount_requested": amount,
        "origin": {"lat": origin[0], "lng": origin[1]} if origin else None,
        "district": district,
        "weights": dict(WEIGHTS),
        "candidates_considered": len(rows),
        "eligible_partner_count": len(accepted),
        "partners": [p.to_dict() for p in top],
        # Ordered by distance because the persuasive case is the *close* branch that
        # cannot help you.
        "why_not": [r.to_dict() for r in rejected[:TOP_N_WHY_NOT]],
        "data_disclaimer": SYNTHETIC_DISCLAIMER,
    }


def _reject_reason(
    partner: ChannelPartner,
    auth: PartnerSchemeAuthorisation | None,
    scheme: Scheme,
    amount: float,
    district: str | None,
    distance_km: float | None,
) -> Rejection | None:
    """Return why this partner cannot take the application, or None if it can.

    Checked in the order a citizen would find most useful: authorisation first,
    because "they don't do this scheme" is the fact that sends people to the wrong
    branch.
    """

    def reject(code: str, text: str) -> Rejection:
        return Rejection(
            partner_id=str(partner.id),
            name=partner.name,
            type=str(partner.type),
            district=partner.district,
            distance_km=distance_km,
            reason_code=code,
            reason=text,
        )

    near = f"is {distance_km} km away but" if distance_km is not None else "is nearby but"

    if auth is None:
        return reject(
            "NOT_AUTHORISED",
            f"{partner.name} {near} is not authorised for the {scheme.official_name}.",
        )

    if not auth.is_currently_accepting:
        return reject(
            "NOT_ACCEPTING",
            f"{partner.name} {near} has paused new {scheme.official_name} "
            "applications because its capacity is exhausted.",
        )

    if auth.min_ticket is not None and amount < float(auth.min_ticket):
        return reject(
            "BELOW_MIN_TICKET",
            f"{partner.name} {near} does not process {scheme.official_name} amounts "
            f"below Rs {float(auth.min_ticket):,.0f}.",
        )

    if auth.max_ticket is not None and amount > float(auth.max_ticket):
        return reject(
            "ABOVE_MAX_TICKET",
            f"{partner.name} {near} processes {scheme.official_name} amounts only up "
            f"to Rs {float(auth.max_ticket):,.0f}.",
        )

    if distance_km is not None and distance_km > MAX_SERVICE_RADIUS_KM:
        return reject(
            "TOO_FAR",
            f"{partner.name} is authorised for the {scheme.official_name} but is "
            f"{distance_km} km away, beyond the {MAX_SERVICE_RADIUS_KM:.0f} km "
            "service radius.",
        )

    if district and auth.service_districts and district not in auth.service_districts:
        return reject(
            "DISTRICT_NOT_SERVED",
            f"{partner.name} {near} does not serve {district} for this scheme "
            f"(it serves {', '.join(auth.service_districts)}).",
        )

    return None


def _score(
    partner: ChannelPartner,
    auth: PartnerSchemeAuthorisation,
    scheme: Scheme,
    distance_km: float | None,
    lat: float | None = None,
    lng: float | None = None,
) -> RoutedPartner:
    components = {
        "distance": {
            "value": distance_km,
            "unit": "km",
            "score": round(_distance_score(distance_km), 4),
            "weight": WEIGHTS["distance"],
        },
        "turnaround": {
            "value": auth.avg_turnaround_days,
            "unit": "days",
            "score": round(_turnaround_score(auth.avg_turnaround_days), 4),
            "weight": WEIGHTS["turnaround"],
        },
        "type_affinity": {
            "value": str(partner.type),
            "unit": "affinity",
            "score": round(_affinity_score(scheme.family, partner.type), 4),
            "weight": WEIGHTS["type_affinity"],
        },
        "load": {
            "value": auth.active_load,
            "unit": "percent_occupied",
            "score": round(_load_score(auth.active_load), 4),
            "weight": WEIGHTS["load"],
        },
    }
    total = sum(c["score"] * c["weight"] for c in components.values())
    for c in components.values():
        c["contribution"] = round(c["score"] * c["weight"], 4)

    return RoutedPartner(
        partner_id=str(partner.id),
        name=partner.name,
        type=str(partner.type),
        parent_org=partner.parent_org,
        ifsc=partner.ifsc,
        address=partner.address,
        district=partner.district,
        state=partner.state,
        pincode=partner.pincode,
        contact=dict(partner.contact or {}),
        lat=lat,
        lng=lng,
        distance_km=distance_km,
        avg_turnaround_days=auth.avg_turnaround_days,
        active_load=auth.active_load,
        min_ticket=float(auth.min_ticket) if auth.min_ticket is not None else None,
        max_ticket=float(auth.max_ticket) if auth.max_ticket is not None else None,
        score=round(total, 4),
        score_breakdown=components,
    )
