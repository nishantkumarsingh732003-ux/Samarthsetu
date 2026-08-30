"""The MoSJE analytics dashboard.

Read-only, admin-gated, and every figure computed from the database on request. There is
no aggregation job and no cached snapshot: at this data volume the queries are cheap,
and a dashboard that can go stale is a dashboard someone will eventually quote from
after it has.
"""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

from app.api.v1.deps import AdminUser, SessionDep
from app.schemas.console import AnalyticsOut
from app.services import analytics, audit

router = APIRouter()


@router.get(
    "/analytics",
    response_model=AnalyticsOut,
    summary="Every figure on the ministry dashboard",
    description=(
        "Computed from the database on every call. Adding one application changes the "
        "funnel, the scheme mix and the coverage map on the next load."
    ),
)
async def get_analytics(user: AdminUser, session: SessionDep) -> AnalyticsOut:
    data = await analytics.snapshot(session)
    await audit.record(
        session,
        actor=user.email,
        action="ANALYTICS_VIEWED",
        entity="dashboard",
        entity_id=None,
        meta={"engine_version": data["engine_version"]},
    )
    await session.commit()
    return AnalyticsOut(**data)


@router.get(
    "/export.csv",
    summary="Download a dashboard section as CSV",
    description=(
        "One section per call so each file has a single, obvious shape. A ministry "
        "analyst opening this in a spreadsheet should not have to unpick a nested export."
    ),
)
async def export_csv(
    user: AdminUser,
    session: SessionDep,
    section: str = Query(
        default="underserved",
        pattern="^(underserved|funnel|scheme_mix|language_mix|status_mix|turnaround)$",
    ),
) -> StreamingResponse:
    data = await analytics.snapshot(session)

    if section == "underserved":
        header = [
            "district", "state", "demand", "partners_within_25km",
            "nearest_authorised_km", "families_unserved",
        ]
        rows = [
            [
                row["district"], row["state"], row["demand"], row["partners_within_25km"],
                row["nearest_authorised_km"], "; ".join(row["families_unserved"]),
            ]
            for row in data["coverage"]["underserved"]
        ]
    elif section == "funnel":
        header = ["stage", "label", "count", "conversion_from_previous"]
        rows = [
            [s["stage"], s["label"], s["count"], s["conversion_from_previous"]]
            for s in data["funnel"]["stages"]
        ]
    elif section == "turnaround":
        header = ["partner_type", "applications", "median_days", "p90_days"]
        rows = [
            [r["partner_type"], r["applications"], r["median_days"], r["p90_days"]]
            for r in data["turnaround"]
        ]
    else:
        header = ["key", "label", "count", "share"]
        rows = [[r["key"], r["label"], r["count"], r["share"]] for r in data[section]]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    writer.writerows(rows)
    buffer.seek(0)

    await audit.record(
        session,
        actor=user.email,
        action="ANALYTICS_EXPORTED",
        entity="dashboard",
        entity_id=section,
        meta={"rows": len(rows)},
    )
    await session.commit()

    return StreamingResponse(
        # utf-8-sig so Excel on Windows opens Devanagari and Tamil labels correctly
        # rather than as mojibake, which is the difference between a usable export and
        # a support ticket.
        iter([buffer.getvalue().encode("utf-8-sig")]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="setu-{section}.csv"'},
    )
