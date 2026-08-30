"""The Channel Partner console.

Every query in this module filters on `user.partner_id`. That is the whole access
control model, and it is expressed as a **WHERE clause rather than a permission check**
on purpose: a forgotten `if` widens a result set silently, a forgotten join condition
returns nothing and is noticed immediately. The failure mode of the safer shape is a
bug you can see.

Two things the officer gets here that a plain queue would not give them:

  - **Why the system routed this application to them**, carried from the eligibility run
    that produced it. The partner sees the rule IDs, not a black box.
  - **A document readiness score with the missing items named**, so they can pick up the
    application that will actually move rather than the oldest one.

And the capacity toggle writes straight back into `partner_scheme_authorisations`, which
is the same table the routing engine hard-filters on. Pausing intake here removes the
branch from citizen routing on the next call.
"""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from setu_rules import rule_messages
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import PartnerUser, SessionDep
from app.models import (
    Application,
    ChannelPartner,
    Citizen,
    MatchRun,
    PartnerSchemeAuthorisation,
    Scheme,
)
from app.models.enums import ApplicationStatus
from app.schemas.console import (
    ApplicantSummary,
    CapacityRequest,
    CapacityResponse,
    CapacityRow,
    PartnerActionRequest,
    QueueItem,
    QueueResponse,
    ReadinessOut,
)
from app.services import applications as application_service
from app.services import audit, readiness

router = APIRouter()

# What each console action means in lifecycle terms. Keeping the mapping here rather
# than letting the console post a raw status means the API surface stays a vocabulary of
# intentions, and `applications.ALLOWED_TRANSITIONS` remains the single arbiter of what
# is legal from where.
ACTIONS: dict[str, ApplicationStatus] = {
    "ACKNOWLEDGE": ApplicationStatus.PARTNER_ACKNOWLEDGED,
    "REQUEST_DOCS": ApplicationStatus.DOCS_REQUESTED,
    "APPRAISE": ApplicationStatus.UNDER_APPRAISAL,
    "SANCTION": ApplicationStatus.SANCTIONED,
    "DISBURSE": ApplicationStatus.DISBURSED,
    "REJECT": ApplicationStatus.REJECTED,
}

# Actions a partner must justify. Rejecting someone without a reason is the behaviour
# this project exists to replace.
REASON_REQUIRED = {"REJECT", "REQUEST_DOCS"}

OPEN_STATUSES = (
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.PARTNER_ACKNOWLEDGED,
    ApplicationStatus.DOCS_REQUESTED,
    ApplicationStatus.UNDER_APPRAISAL,
)


async def _partner(session: AsyncSession, partner_id) -> ChannelPartner:
    partner = (
        await session.execute(select(ChannelPartner).where(ChannelPartner.id == partner_id))
    ).scalar_one_or_none()
    if partner is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "This login is not attached to a partner.")
    return partner


def _sla(days_open: int, turnaround: int | None) -> tuple[int | None, str]:
    """Where this application sits against the partner's own stated turnaround.

    Measured against `avg_turnaround_days` for the scheme, which the partner sets — so
    the clock is their commitment, not a number we invented for them.
    """
    if turnaround is None:
        return None, "UNKNOWN"
    if days_open > turnaround:
        return turnaround, "BREACHED"
    if days_open >= turnaround - 1:
        return turnaround, "DUE"
    return turnaround, "ON_TRACK"


@router.get(
    "/queue",
    response_model=QueueResponse,
    summary="Applications routed to this partner",
    description=(
        "Scoped to the signed-in partner by a WHERE clause, not a permission check. "
        "Each item carries the rule-engine verdict that routed it here and a document "
        "readiness score naming what is still missing."
    ),
)
async def queue(
    user: PartnerUser,
    session: SessionDep,
    status_filter: str | None = Query(default=None, alias="status"),
    only_open: bool = Query(default=False),
    limit: int = Query(default=100, ge=1, le=500),
    language: str = Query(default="en", pattern="^(en|hi|mr|bn|ta|te)$"),
) -> QueueResponse:
    partner = await _partner(session, user.partner_id)

    query = (
        select(Application)
        .options(selectinload(Application.documents))
        # The access boundary.
        .where(Application.partner_id == user.partner_id)
        .order_by(Application.created_at.desc())
    )
    if status_filter:
        try:
            query = query.where(Application.status == ApplicationStatus(status_filter))
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"Unknown status: {status_filter}"
            ) from exc
    elif only_open:
        query = query.where(Application.status.in_(OPEN_STATUSES))

    rows = list((await session.execute(query.limit(limit))).scalars())

    # Counts across the whole queue, not just the filtered page — an officer filtering
    # to REJECTED still needs to see that 12 applications are waiting.
    counts: dict[str, int] = {}
    for status_value, count in await session.execute(
        select(Application.status, func.count())
        .where(Application.partner_id == user.partner_id)
        .group_by(Application.status)
    ):
        counts[str(status_value)] = count

    # Everything the loop needs, fetched in four queries rather than four per row. A
    # queue of 100 applications is an ordinary Monday for a busy branch, and a
    # per-row lookup turns that into 400 round trips.
    schemes = {
        scheme.id: scheme
        for scheme in (await session.execute(select(Scheme))).scalars()
    }
    citizens = {
        citizen.id: citizen
        for citizen in (
            await session.execute(
                select(Citizen).where(Citizen.id.in_({r.citizen_id for r in rows}))
            )
        ).scalars()
    } if rows else {}
    auths = {
        auth.scheme_id: auth
        for auth in (
            await session.execute(
                select(PartnerSchemeAuthorisation).where(
                    PartnerSchemeAuthorisation.partner_id == user.partner_id
                )
            )
        ).scalars()
    }
    run_ids = {r.match_run_id for r in rows if r.match_run_id}
    runs = {
        run.id: run
        for run in (
            await session.execute(select(MatchRun).where(MatchRun.id.in_(run_ids)))
        ).scalars()
    } if run_ids else {}

    messages = rule_messages(language)

    items: list[QueueItem] = []
    now = datetime.now(UTC)
    for application in rows:
        scheme = schemes[application.scheme_id]
        citizen = citizens.get(application.citizen_id)
        auth = auths.get(scheme.id)

        verdict, matched = None, []
        run = runs.get(application.match_run_id) if application.match_run_id else None
        if run:
            for result in run.results:
                if result.get("scheme_code") == scheme.code:
                    verdict = result.get("verdict")
                    # The stored run holds the reasons in the *citizen's* language,
                    # which is right for the citizen and unreadable for an officer who
                    # does not share it. Rule IDs are stable and versioned, so the
                    # reason is rebuilt in the console's language rather than replayed.
                    matched = [
                        {
                            **reason,
                            "message": messages.get(reason["rule_id"], reason["message"]),
                        }
                        for reason in result.get("matched_because", [])
                    ]
                    break

        days_open = (now - application.created_at).days if application.created_at else 0
        sla_days, sla_state = _sla(
            days_open, auth.avg_turnaround_days if auth else None
        )

        items.append(
            QueueItem(
                reference_no=application.reference_no,
                status=str(application.status),
                scheme_code=scheme.code,
                scheme_name=scheme.official_name,
                family=str(scheme.family),
                amount_requested=float(application.amount_requested)
                if application.amount_requested is not None
                else None,
                submitted_at=application.created_at.isoformat()
                if application.created_at
                else None,
                days_open=days_open,
                sla_days=sla_days,
                sla_state=sla_state,
                applicant=ApplicantSummary(
                    display_name=citizen.display_name if citizen else None,
                    # Masked at ingestion and never held in full. The branch does the
                    # real KYC with the document in hand.
                    gov_id_type=str(citizen.gov_id_type)
                    if citizen and citizen.gov_id_type
                    else None,
                    gov_id_last4=citizen.gov_id_last4 if citizen else None,
                    phone_last4=citizen.phone_last4 if citizen else None,
                    district=citizen.district if citizen else None,
                    state=citizen.state if citizen else None,
                    preferred_language=citizen.preferred_language if citizen else "en",
                )
                if citizen
                else ApplicantSummary(),
                readiness=ReadinessOut(
                    **readiness.assess(application, scheme, str(partner.type)).to_dict()
                ),
                verdict=verdict,
                matched_because=matched,
                engine_version=application.engine_version,
            )
        )

    # CLAUDE.md rule 4: a full log of who read what. A queue read is a bulk read of
    # citizen data and is recorded as one.
    await audit.record(
        session,
        actor=user.email,
        action="PARTNER_QUEUE_VIEWED",
        entity="channel_partner",
        entity_id=str(user.partner_id),
        meta={"returned": len(items), "status_filter": status_filter, "only_open": only_open},
    )
    await session.commit()

    return QueueResponse(
        partner_id=str(partner.id),
        partner_name=partner.name,
        is_currently_accepting=any(a.is_currently_accepting for a in auths.values()),
        total=sum(counts.values()),
        items=items,
        counts_by_status=counts,
    )


@router.post(
    "/applications/{reference_no}/action",
    response_model=QueueItem,
    summary="Accept, request documents, appraise, sanction, or reject",
    description=(
        "Every action writes an audit row naming the officer. Rejecting or requesting "
        "documents requires a reason — telling a citizen 'no' without saying why is the "
        "behaviour this project exists to replace."
    ),
)
async def act(
    reference_no: str,
    payload: PartnerActionRequest,
    user: PartnerUser,
    session: SessionDep,
) -> QueueItem:
    application = (
        await session.execute(
            select(Application)
            .options(selectinload(Application.documents))
            .where(
                Application.reference_no == reference_no,
                # Scoped here too: another partner's reference is a 404, not a 403,
                # because confirming it exists would leak that it exists.
                Application.partner_id == user.partner_id,
            )
        )
    ).scalar_one_or_none()
    if application is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No application with that reference number.")

    if payload.action in REASON_REQUIRED and not (payload.reason or "").strip():
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"{payload.action} needs a reason the citizen can read and act on.",
        )

    try:
        await application_service.transition(
            session,
            application,
            ACTIONS[payload.action],
            actor=f"partner:{user.email}",
            reason=payload.reason,
        )
    except application_service.IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    await session.commit()

    # Re-read through the queue builder so the console gets exactly the shape it renders.
    refreshed = await queue(
        user, session, status_filter=None, only_open=False, limit=500, language="en"
    )
    for item in refreshed.items:
        if item.reference_no == reference_no:
            return item
    raise HTTPException(status.HTTP_404_NOT_FOUND, "No application with that reference number.")


@router.get(
    "/capacity",
    response_model=CapacityResponse,
    summary="What this partner is currently accepting",
)
async def get_capacity(user: PartnerUser, session: SessionDep) -> CapacityResponse:
    partner = await _partner(session, user.partner_id)
    rows = (
        await session.execute(
            select(PartnerSchemeAuthorisation, Scheme)
            .join(Scheme, Scheme.id == PartnerSchemeAuthorisation.scheme_id)
            .where(PartnerSchemeAuthorisation.partner_id == user.partner_id)
            .order_by(Scheme.code)
        )
    ).all()

    return CapacityResponse(
        partner_id=str(partner.id),
        partner_name=partner.name,
        rows=[
            CapacityRow(
                scheme_code=scheme.code,
                scheme_name=scheme.official_name,
                family=str(scheme.family),
                is_currently_accepting=auth.is_currently_accepting,
                min_ticket=float(auth.min_ticket) if auth.min_ticket is not None else None,
                max_ticket=float(auth.max_ticket) if auth.max_ticket is not None else None,
                avg_turnaround_days=auth.avg_turnaround_days,
                active_load=auth.active_load,
            )
            for auth, scheme in rows
        ],
    )


@router.patch(
    "/capacity",
    response_model=CapacityResponse,
    summary="Pause intake or change the ticket ceiling",
    description=(
        "Writes to the same `partner_scheme_authorisations` rows the routing engine "
        "hard-filters on, so pausing here removes this branch from citizen routing on "
        "the next call. Nothing is cached longer than the routing cache TTL."
    ),
)
async def set_capacity(
    payload: CapacityRequest,
    user: PartnerUser,
    session: SessionDep,
) -> CapacityResponse:
    if payload.is_currently_accepting is None and payload.max_ticket is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Nothing to change: set is_currently_accepting, max_ticket, or both.",
        )

    query = select(PartnerSchemeAuthorisation).where(
        PartnerSchemeAuthorisation.partner_id == user.partner_id
    )
    if payload.scheme_code:
        scheme = (
            await session.execute(select(Scheme).where(Scheme.code == payload.scheme_code))
        ).scalar_one_or_none()
        if scheme is None:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, f"Unknown scheme code: {payload.scheme_code}"
            )
        query = query.where(PartnerSchemeAuthorisation.scheme_id == scheme.id)

    rows = list((await session.execute(query)).scalars())
    if not rows:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "This partner has no authorisation matching that filter."
        )

    changed: list[dict] = []
    for auth in rows:
        before = {
            "is_currently_accepting": auth.is_currently_accepting,
            "max_ticket": float(auth.max_ticket) if auth.max_ticket is not None else None,
        }
        if payload.is_currently_accepting is not None:
            auth.is_currently_accepting = payload.is_currently_accepting
        if payload.max_ticket is not None:
            auth.max_ticket = payload.max_ticket
        changed.append({"authorisation_id": str(auth.id), "before": before})

    await audit.record(
        session,
        actor=user.email,
        action="PARTNER_CAPACITY_CHANGED",
        entity="channel_partner",
        entity_id=str(user.partner_id),
        meta={
            "scheme_code": payload.scheme_code,
            "is_currently_accepting": payload.is_currently_accepting,
            "max_ticket": payload.max_ticket,
            "rows_changed": len(rows),
            # The previous values, so a capacity change is reversible from the log alone.
            "previous": changed,
        },
    )
    await session.commit()

    # The routing cache would otherwise serve the old capacity for its TTL, which on a
    # live demo is exactly the wrong moment to be stale.
    from app.core import cache

    await cache.invalidate_routing()

    return await get_capacity(user, session)
