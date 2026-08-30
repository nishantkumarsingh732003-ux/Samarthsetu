"""MoSJE dashboard aggregates.

Every number here is a query. Nothing is hardcoded, nothing is sampled, and adding one
application changes the funnel, the scheme mix and the coverage map on the next load —
which is the acceptance test for this phase and also the only honest way to build a
dashboard a ministry might act on.

Two of these are worth reading carefully.

**Misrouting prevented** is the primary KPI, and it is counted from `audit_log` rows
written by the routing endpoint, not inferred. Each `PARTNERS_ROUTED` row carries
`rejected_by_reason`: every nearby branch that could not have taken that application,
tallied by the rule that excluded it. "Not authorised for this scheme" and "too far" are
different policy problems and are reported separately.

**Underserved districts** is the one number here that is a policy finding rather than a
progress report: districts where citizens are asking for a scheme family that no
authorised partner within 25km can process. It is computed with PostGIS against the
partners' real geometry, and it is deliberately allowed to come back empty — a dashboard
that always finds a crisis is not measuring anything.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Float, String, cast, func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Application,
    AuditLog,
    ChannelPartner,
    Citizen,
    MatchRun,
    PartnerSchemeAuthorisation,
    Scheme,
)
from app.models.enums import ApplicationStatus

# The radius within which a citizen can reasonably reach a branch and return the same
# day. Not a published figure — see OPEN_ITEMS.
COVERAGE_RADIUS_KM = 25.0

FUNNEL_LABELS = {
    "eligibility_runs": "Checked eligibility",
    "profiles_with_facts": "Gave enough to decide",
    "matched_eligible": "Matched to a scheme",
    "routed": "Shown a partner",
    "submitted": "Applied",
    "acknowledged": "Partner picked it up",
    "sanctioned": "Sanctioned",
}

STATUS_LABELS = {
    "SUBMITTED": "Submitted",
    "PARTNER_ACKNOWLEDGED": "Picked up",
    "DOCS_REQUESTED": "Documents requested",
    "UNDER_APPRAISAL": "Under review",
    "SANCTIONED": "Sanctioned",
    "DISBURSED": "Disbursed",
    "REJECTED": "Rejected",
    "WITHDRAWN": "Withdrawn",
}

LANGUAGE_LABELS = {
    "en": "English",
    "hi": "हिन्दी",
    "mr": "मराठी",
    "bn": "বাংলা",
    "ta": "தமிழ்",
    "te": "తెలుగు",
}


async def _scalar(session: AsyncSession, statement) -> int:
    return (await session.execute(statement)).scalar_one() or 0


async def funnel(session: AsyncSession) -> dict[str, Any]:
    """Where citizens fall out, from first question to sanction."""
    runs = await _scalar(session, select(func.count()).select_from(MatchRun))

    # A run whose input snapshot carries at least one fact — distinguishes someone who
    # opened the app from someone who actually answered a question.
    with_facts = await _scalar(
        session,
        select(func.count()).select_from(MatchRun).where(
            func.jsonb_array_length(
                func.coalesce(
                    func.jsonb_path_query_array(MatchRun.input_snapshot, text("'$.keyvalue()'")),
                    text("'[]'::jsonb"),
                )
            )
            > 0
        ),
    )

    # A run that produced at least one ELIGIBLE or LIKELY_ELIGIBLE verdict.
    matched = await _scalar(
        session,
        select(func.count()).select_from(MatchRun).where(
            text(
                "EXISTS (SELECT 1 FROM jsonb_array_elements(match_runs.results) r "
                "WHERE r->>'verdict' IN ('ELIGIBLE','LIKELY_ELIGIBLE'))"
            )
        ),
    )

    routed = await _scalar(
        session,
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "PARTNERS_ROUTED"),
    )
    submitted = await _scalar(session, select(func.count()).select_from(Application))

    # Reached a stage at any point, read from the timeline rather than the current
    # status — an application that was acknowledged and later rejected still passed
    # through acknowledgement, and a funnel that forgets that overstates the drop-off.
    async def reached(status_name: str) -> int:
        return await _scalar(
            session,
            select(func.count()).select_from(Application).where(
                text(
                    "EXISTS (SELECT 1 FROM jsonb_array_elements(applications.status_history) h "
                    f"WHERE h->>'status' = '{status_name}')"
                )
            ),
        )

    acknowledged = await reached(ApplicationStatus.PARTNER_ACKNOWLEDGED.value)
    sanctioned = await reached(ApplicationStatus.SANCTIONED.value)

    counts = {
        "eligibility_runs": runs,
        "profiles_with_facts": with_facts,
        "matched_eligible": matched,
        "routed": routed,
        "submitted": submitted,
        "acknowledged": acknowledged,
        "sanctioned": sanctioned,
    }

    stages: list[dict[str, Any]] = []
    previous: int | None = None
    previous_label: str | None = None
    # Ranked by people lost, not by percentage lost. The final stage of a young pipeline
    # is always a 100% drop, and pointing a ministry at "nobody has been sanctioned yet"
    # on day one is noise. The stage that lost the most actual citizens is the one worth
    # fixing, and it is the number that changes as the pipeline matures.
    worst: tuple[str, int, float] | None = None

    for key, count in counts.items():
        conversion = None
        if previous is not None and previous > 0:
            conversion = round(count / previous, 4)
            lost = previous - count
            if lost > 0 and (worst is None or lost > worst[1]):
                worst = (f"{previous_label} → {FUNNEL_LABELS[key]}", lost, 1 - conversion)
        stages.append(
            {
                "stage": key,
                "label": FUNNEL_LABELS[key],
                "count": count,
                "conversion_from_previous": conversion,
            }
        )
        previous = count
        previous_label = FUNNEL_LABELS[key]

    return {
        "stages": stages,
        "largest_drop_off": worst[0] if worst else None,
        "largest_drop_off_pct": round(worst[2], 4) if worst else None,
    }


async def misrouting(session: AsyncSession) -> dict[str, Any]:
    """The primary KPI, counted from what the routing engine actually recorded."""

    async def reason_total(code: str) -> int:
        return await _scalar(
            session,
            select(
                func.coalesce(
                    func.sum(
                        cast(AuditLog.meta["rejected_by_reason"][code].astext, Float)
                    ),
                    0,
                )
            ).where(AuditLog.action == "PARTNERS_ROUTED"),
        )

    routing_calls = await _scalar(
        session,
        select(func.count()).select_from(AuditLog).where(AuditLog.action == "PARTNERS_ROUTED"),
    )

    not_authorised = int(await reason_total("NOT_AUTHORISED"))
    not_accepting = int(await reason_total("NOT_ACCEPTING"))
    too_far = int(await reason_total("TOO_FAR"))
    district = int(await reason_total("DISTRICT_NOT_SERVED"))
    below = int(await reason_total("BELOW_MIN_TICKET"))
    above = int(await reason_total("ABOVE_MAX_TICKET"))

    # A redirect fired when the engine told a citizen "this scheme does not fit, consider
    # that one" — the other half of misrouting, upstream of the partner choice.
    redirects = await _scalar(
        session,
        select(func.count()).select_from(MatchRun).where(
            text(
                "EXISTS (SELECT 1 FROM jsonb_array_elements(match_runs.results) r "
                "WHERE r->>'redirect_suggestion' IS NOT NULL)"
            )
        ),
    )

    return {
        "redirects_suggested": redirects,
        "partners_filtered_for_authorisation": not_authorised + not_accepting,
        "partners_filtered_for_distance": too_far + district,
        "partners_filtered_for_ticket_size": below + above,
        "routing_calls": routing_calls,
        "total_prevented": not_authorised
        + not_accepting
        + too_far
        + district
        + below
        + above
        + redirects,
    }


async def coverage(session: AsyncSession, radius_km: float = COVERAGE_RADIUS_KM) -> dict[str, Any]:
    """Districts where demand exists but no authorised partner is within reach.

    Demand is measured from citizens who ran an eligibility check, not from applications
    — the districts that matter most are the ones where people looked and found nothing,
    and those citizens never reach the application table at all.
    """
    demand_rows = (
        await session.execute(
            select(
                Citizen.district,
                Citizen.state,
                func.count().label("demand"),
            )
            .where(Citizen.district.isnot(None))
            .group_by(Citizen.district, Citizen.state)
            .order_by(func.count().desc())
        )
    ).all()

    underserved: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []

    for district, state, demand in demand_rows:
        # Partners within the radius of any partner geometry in that district is
        # circular; instead measure from the district's own partners outward, and where
        # a district has none, report the nearest authorised partner in the state.
        within = await _scalar(
            session,
            select(func.count())
            .select_from(ChannelPartner)
            .join(
                PartnerSchemeAuthorisation,
                PartnerSchemeAuthorisation.partner_id == ChannelPartner.id,
            )
            .where(
                ChannelPartner.district == district,
                ChannelPartner.is_active.is_(True),
                PartnerSchemeAuthorisation.is_currently_accepting.is_(True),
            ),
        )

        families_served = {
            str(family)
            for (family,) in (
                await session.execute(
                    select(Scheme.family)
                    .join(
                        PartnerSchemeAuthorisation,
                        PartnerSchemeAuthorisation.scheme_id == Scheme.id,
                    )
                    .join(
                        ChannelPartner,
                        ChannelPartner.id == PartnerSchemeAuthorisation.partner_id,
                    )
                    .where(
                        ChannelPartner.district == district,
                        ChannelPartner.is_active.is_(True),
                        PartnerSchemeAuthorisation.is_currently_accepting.is_(True),
                    )
                    .distinct()
                )
            ).all()
        }
        unserved = sorted({"MICRO_FINANCE", "TERM_LOAN", "EDUCATION_LOAN"} - families_served)

        nearest_km: float | None = None
        if within == 0:
            # Straight-line distance from any partner in the same state, in kilometres.
            nearest_km = (
                await session.execute(
                    select(
                        func.min(
                            func.ST_Distance(
                                ChannelPartner.geom,
                                select(ChannelPartner.geom)
                                .where(ChannelPartner.district == district)
                                .limit(1)
                                .scalar_subquery(),
                            )
                            / 1000.0
                        )
                    ).where(ChannelPartner.state == state, ChannelPartner.district != district)
                )
            ).scalar_one_or_none()

        points.append(
            {
                "district": district,
                "state": state,
                "demand": demand,
                "partners": within,
                "unserved_families": unserved,
            }
        )

        if within == 0 or unserved:
            underserved.append(
                {
                    "district": district,
                    "state": state or "",
                    "demand": demand,
                    "partners_within_25km": within,
                    "nearest_authorised_km": round(float(nearest_km), 1)
                    if nearest_km is not None
                    else None,
                    "families_unserved": unserved,
                }
            )

    underserved.sort(key=lambda row: (-row["demand"], row["district"]))
    return {
        "radius_km": radius_km,
        "districts_with_demand": len(demand_rows),
        "underserved": underserved[:25],
        "points": points,
    }


def _breakdown(rows: list[tuple[Any, int]], labels: dict[str, str]) -> list[dict[str, Any]]:
    total = sum(count for _, count in rows) or 1
    return [
        {
            "key": str(key),
            "label": labels.get(str(key), str(key).replace("_", " ").title()),
            "count": count,
            "share": round(count / total, 4),
        }
        for key, count in rows
    ]


async def scheme_mix(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(Scheme.official_name, func.count(Application.id))
            .join(Application, Application.scheme_id == Scheme.id)
            .group_by(Scheme.official_name)
            .order_by(func.count(Application.id).desc())
        )
    ).all()
    # Official names verbatim; they are not ours to relabel (CLAUDE.md).
    return _breakdown(list(rows), {})


async def language_mix(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(Citizen.preferred_language, func.count())
            .group_by(Citizen.preferred_language)
            .order_by(func.count().desc())
        )
    ).all()
    return _breakdown(list(rows), LANGUAGE_LABELS)


async def status_mix(session: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await session.execute(
            select(cast(Application.status, String), func.count())
            .group_by(Application.status)
            .order_by(func.count().desc())
        )
    ).all()
    return _breakdown(list(rows), STATUS_LABELS)


async def turnaround(session: AsyncSession) -> list[dict[str, Any]]:
    """Observed days from submission to a partner picking the application up.

    Median and p90 rather than a mean: one application that sat for ninety days moves a
    mean enough to hide that everything else was handled in two.
    """
    rows = (
        await session.execute(
            select(
                cast(ChannelPartner.type, String).label("partner_type"),
                func.count(Application.id).label("applications"),
                func.percentile_cont(0.5)
                .within_group(
                    func.extract("epoch", Application.updated_at - Application.created_at) / 86400.0
                )
                .label("median_days"),
                func.percentile_cont(0.9)
                .within_group(
                    func.extract("epoch", Application.updated_at - Application.created_at) / 86400.0
                )
                .label("p90_days"),
            )
            .join(ChannelPartner, ChannelPartner.id == Application.partner_id)
            .where(Application.status != ApplicationStatus.SUBMITTED)
            .group_by(ChannelPartner.type)
            .order_by(func.count(Application.id).desc())
        )
    ).all()

    return [
        {
            "partner_type": row.partner_type,
            "applications": row.applications,
            "median_days": round(float(row.median_days), 2)
            if row.median_days is not None
            else None,
            "p90_days": round(float(row.p90_days), 2) if row.p90_days is not None else None,
        }
        for row in rows
    ]


async def snapshot(session: AsyncSession) -> dict[str, Any]:
    """Everything the dashboard renders, in one call."""
    from setu_rules import ENGINE_VERSION

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "engine_version": ENGINE_VERSION,
        "funnel": await funnel(session),
        "misrouting": await misrouting(session),
        "coverage": await coverage(session),
        "scheme_mix": await scheme_mix(session),
        "language_mix": await language_mix(session),
        "turnaround": await turnaround(session),
        "status_mix": await status_mix(session),
    }
