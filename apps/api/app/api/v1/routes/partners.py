"""Channel Partner routing and lookup."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status
from geoalchemy2 import Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import SessionDep
from app.core import cache
from app.models import ChannelPartner, PartnerSchemeAuthorisation
from app.schemas.match import PartnerDetailOut, RouteRequest, RouteResponse
from app.services import audit, routing

router = APIRouter()


async def _audit_routing(
    session: AsyncSession,
    request: Request,
    payload: RouteRequest,
    result: dict,
    *,
    from_cache: bool,
) -> None:
    """One audit row per routing decision, cached or not.

    `rejected_by_reason` is the anti-misrouting KPI in its raw form: every nearby branch
    that could not have taken this application, counted by the rule that excluded it.
    Storing the breakdown rather than a single total is what lets /admin say "authorised
    for the wrong scheme" separately from "too far", which are different policy problems.
    """
    # From the routing result, which counts every exclusion. `why_not` is truncated for
    # the citizen UI and would undercount this badly.
    by_reason = dict(result.get("rejected_by_reason") or {})

    await audit.record(
        session,
        actor=request.client.host if request.client else "unknown",
        action="PARTNERS_ROUTED",
        entity="scheme",
        entity_id=payload.scheme_code,
        meta={
            "amount": payload.amount,
            "district": payload.district,
            "match_run_id": payload.match_run_id,
            "eligible_partner_count": result["eligible_partner_count"],
            "rejected_count": result["candidates_considered"]
            - result["eligible_partner_count"],
            "rejected_by_reason": by_reason,
            "routing_version": result["routing_version"],
            "served_from_cache": from_cache,
        },
    )



@router.post(
    "/route",
    response_model=RouteResponse,
    summary="Rank Channel Partners authorised for a scheme",
    description=(
        "Hard-filters to partners actually authorised for this scheme at this ticket "
        "size, ranks them on a transparent composite score with every component "
        "returned separately, and reports the nearest rejected branches in `why_not` "
        "with the exact rule that excluded each one."
    ),
)
async def route(
    payload: RouteRequest,
    request: Request,
    session: SessionDep,
) -> RouteResponse:
    key = cache.routing_key(
        payload.scheme_code, payload.amount, payload.lat, payload.lng, payload.district
    )
    cached = await cache.cache_get(key)
    if cached is not None:
        cached["cached"] = True
        # A cached response is still a routing decision shown to a citizen. Auditing
        # only on a cache miss would undercount the anti-misrouting KPI exactly when
        # the system is busiest, and would leave a gap in the "who read what" trail
        # that CLAUDE.md rule 4 requires.
        await _audit_routing(session, request, payload, cached, from_cache=True)
        await session.commit()
        return RouteResponse(**cached)

    try:
        result = await routing.find_partners(
            session,
            scheme_code=payload.scheme_code,
            amount=payload.amount,
            lat=payload.lat,
            lng=payload.lng,
            district=payload.district,
        )
    except routing.SchemeNotFound as exc:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Unknown scheme code: {exc}"
        ) from exc
    except routing.OriginUnknown as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    await _audit_routing(session, request, payload, result, from_cache=False)
    await session.commit()

    await cache.cache_set(key, result)
    result["cached"] = False
    return RouteResponse(**result)


@router.get(
    "/{partner_id}",
    response_model=PartnerDetailOut,
    summary="Channel Partner detail with its full authorisation matrix",
)
async def get_partner(
    partner_id: str,
    request: Request,
    session: SessionDep,
) -> PartnerDetailOut:
    try:
        pid = uuid.UUID(partner_id)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"partner_id is not a UUID: {exc}"
        ) from exc

    as_geometry = cast(ChannelPartner.geom, Geometry)
    row = (
        await session.execute(
            select(
                ChannelPartner,
                func.ST_Y(as_geometry),
                func.ST_X(as_geometry),
            )
            .options(
                selectinload(ChannelPartner.authorisations).selectinload(
                    PartnerSchemeAuthorisation.scheme
                )
            )
            .where(ChannelPartner.id == pid)
        )
    ).first()

    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No such Channel Partner")

    partner, lat, lng = row

    await audit.record(
        session,
        actor=request.client.host if request.client else "unknown",
        action="PARTNER_READ",
        entity="channel_partner",
        entity_id=str(partner.id),
    )
    await session.commit()

    return PartnerDetailOut(
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
        lat=float(lat) if lat is not None else None,
        lng=float(lng) if lng is not None else None,
        is_active=partner.is_active,
        authorisations=[
            {
                "scheme_code": a.scheme.code,
                "scheme_name": a.scheme.official_name,
                "family": str(a.scheme.family),
                "min_ticket": float(a.min_ticket) if a.min_ticket is not None else None,
                "max_ticket": float(a.max_ticket) if a.max_ticket is not None else None,
                "is_currently_accepting": a.is_currently_accepting,
                "avg_turnaround_days": a.avg_turnaround_days,
                "active_load": a.active_load,
                "service_districts": list(a.service_districts or []),
            }
            for a in sorted(partner.authorisations, key=lambda a: a.scheme.code)
        ],
        data_disclaimer=routing.SYNTHETIC_DISCLAIMER,
    )
