"""Applications: reference numbers, submission, and the status timeline.

An application snapshots the `match_run_id` and `engine_version` that produced it, so a
sanction decision can be replayed against the exact rules that were live when the
citizen applied — even after the YAML has changed. That is what makes the governance
claim testable rather than rhetorical.

The reference number is designed to be read aloud at a branch counter over a bad phone
line: SETU-2026-MH-000431.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Application, ChannelPartner, Scheme
from app.models.enums import ApplicationStatus
from app.services import audit, notifications

# Two-letter codes so the reference number says where the application was raised.
STATE_CODES: dict[str, str] = {
    "Andhra Pradesh": "AP", "Assam": "AS", "Bihar": "BR", "Chhattisgarh": "CG",
    "Delhi": "DL", "Gujarat": "GJ", "Haryana": "HR", "Himachal Pradesh": "HP",
    "Jharkhand": "JH", "Karnataka": "KA", "Kerala": "KL", "Madhya Pradesh": "MP",
    "Maharashtra": "MH", "Odisha": "OD", "Punjab": "PB", "Rajasthan": "RJ",
    "Tamil Nadu": "TN", "Telangana": "TG", "Uttar Pradesh": "UP", "Uttarakhand": "UK",
    "West Bengal": "WB",
}

# Which transitions are legal. A status timeline that accepts anything is a log, not a
# model — a partner cannot sanction an application it never acknowledged.
ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    ApplicationStatus.DRAFT: frozenset(
        {ApplicationStatus.SUBMITTED, ApplicationStatus.WITHDRAWN}
    ),
    ApplicationStatus.SUBMITTED: frozenset(
        {
            ApplicationStatus.PARTNER_ACKNOWLEDGED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.PARTNER_ACKNOWLEDGED: frozenset(
        {
            ApplicationStatus.DOCS_REQUESTED,
            ApplicationStatus.UNDER_APPRAISAL,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.DOCS_REQUESTED: frozenset(
        {
            ApplicationStatus.UNDER_APPRAISAL,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.UNDER_APPRAISAL: frozenset(
        {
            ApplicationStatus.SANCTIONED,
            ApplicationStatus.DOCS_REQUESTED,
            ApplicationStatus.REJECTED,
            ApplicationStatus.WITHDRAWN,
        }
    ),
    ApplicationStatus.SANCTIONED: frozenset(
        {ApplicationStatus.DISBURSED, ApplicationStatus.WITHDRAWN}
    ),
    # Terminal.
    ApplicationStatus.DISBURSED: frozenset(),
    ApplicationStatus.REJECTED: frozenset(),
    ApplicationStatus.WITHDRAWN: frozenset(),
}


# Transitions a citizen is told about, and the template used. WITHDRAWN is absent on
# purpose: the citizen withdrew, so telling them they withdrew is noise.
NOTIFIED_TRANSITIONS: dict[ApplicationStatus, str] = {
    ApplicationStatus.PARTNER_ACKNOWLEDGED: "PARTNER_ACKNOWLEDGED",
    ApplicationStatus.DOCS_REQUESTED: "DOCS_REQUESTED",
    ApplicationStatus.UNDER_APPRAISAL: "UNDER_APPRAISAL",
    ApplicationStatus.SANCTIONED: "SANCTIONED",
    ApplicationStatus.DISBURSED: "DISBURSED",
    ApplicationStatus.REJECTED: "REJECTED",
}


class IllegalTransition(ValueError):
    """A status change that the lifecycle does not allow."""


class ApplicationNotFound(LookupError):
    pass


def state_code(state: str | None) -> str:
    """Two letters for the reference number. Unknown states get XX rather than a guess."""
    return STATE_CODES.get((state or "").strip(), "XX")


async def next_reference_no(session: AsyncSession, state: str | None) -> str:
    """SETU-<year>-<state>-<serial>, serial per year and state.

    The serial is derived from a count rather than a sequence, which is fine at this
    scale and keeps the number meaningful. A unique constraint on `reference_no` is the
    real guard against a collision under concurrency.
    """
    year = datetime.now(UTC).year
    code = state_code(state)
    prefix = f"SETU-{year}-{code}-"

    used = (
        await session.execute(
            select(func.count()).select_from(Application).where(
                Application.reference_no.like(f"{prefix}%")
            )
        )
    ).scalar_one()

    return f"{prefix}{used + 1:06d}"


def _entry(status: ApplicationStatus, actor: str, reason: str | None) -> dict[str, Any]:
    return {
        "status": str(status),
        "actor": actor,
        "at": datetime.now(UTC).isoformat(),
        "reason": reason,
    }


async def create_application(
    session: AsyncSession,
    *,
    citizen_id: uuid.UUID,
    scheme_code: str,
    partner_id: uuid.UUID | None,
    amount_requested: float | None,
    match_run_id: uuid.UUID | None,
    engine_version: str | None,
    actor: str = "citizen",
) -> Application:
    """Create a submitted application and return it."""
    scheme = (
        await session.execute(select(Scheme).where(Scheme.code == scheme_code))
    ).scalar_one_or_none()
    if scheme is None:
        raise ApplicationNotFound(f"Unknown scheme code: {scheme_code}")

    state: str | None = None
    if partner_id is not None:
        partner = (
            await session.execute(
                select(ChannelPartner).where(ChannelPartner.id == partner_id)
            )
        ).scalar_one_or_none()
        if partner is None:
            raise ApplicationNotFound("Unknown Channel Partner")
        state = partner.state

    reference_no = await next_reference_no(session, state)

    application = Application(
        citizen_id=citizen_id,
        scheme_id=scheme.id,
        partner_id=partner_id,
        status=ApplicationStatus.SUBMITTED,
        amount_requested=amount_requested,
        reference_no=reference_no,
        # The decision this application rests on, and the engine that made it.
        match_run_id=match_run_id,
        engine_version=engine_version,
        status_history=[
            _entry(ApplicationStatus.DRAFT, actor, None),
            _entry(ApplicationStatus.SUBMITTED, actor, None),
        ],
    )
    session.add(application)
    await session.flush()

    await audit.record(
        session,
        actor=actor,
        action="APPLICATION_SUBMITTED",
        entity="application",
        entity_id=str(application.id),
        meta={
            "reference_no": reference_no,
            "scheme_code": scheme_code,
            "partner_id": str(partner_id) if partner_id else None,
            "match_run_id": str(match_run_id) if match_run_id else None,
            "engine_version": engine_version,
        },
    )

    # The citizen leaves with a reference number on screen; this is the copy they can
    # come back to. It never raises — a message that cannot be delivered must not roll
    # back the application it is reporting on.
    await notifications.notify(
        session, event="APPLICATION_SUBMITTED", application=application, actor=actor
    )
    return application


async def get_by_reference(session: AsyncSession, reference_no: str) -> Application:
    application = (
        await session.execute(
            select(Application).where(Application.reference_no == reference_no)
        )
    ).scalar_one_or_none()
    if application is None:
        raise ApplicationNotFound(reference_no)
    return application


async def transition(
    session: AsyncSession,
    application: Application,
    to_status: ApplicationStatus,
    actor: str,
    reason: str | None = None,
) -> Application:
    """Move an application along its lifecycle, recording who and why."""
    allowed = ALLOWED_TRANSITIONS.get(application.status, frozenset())
    if to_status not in allowed:
        raise IllegalTransition(
            f"{application.status} cannot become {to_status}. "
            f"Allowed from here: {', '.join(sorted(str(s) for s in allowed)) or 'nothing'}."
        )

    application.status = to_status
    # Reassigned rather than appended: SQLAlchemy does not track in-place JSONB mutation.
    application.status_history = [*application.status_history, _entry(to_status, actor, reason)]

    await audit.record(
        session,
        actor=actor,
        action="APPLICATION_STATUS_CHANGED",
        entity="application",
        entity_id=str(application.id),
        meta={
            "reference_no": application.reference_no,
            "to_status": str(to_status),
            "reason": reason,
        },
    )

    # Silence is never a status. Every transition the citizen would want to know about
    # has a template; anything else passes through without one rather than inventing
    # copy nobody reviewed.
    event = NOTIFIED_TRANSITIONS.get(to_status)
    if event:
        await notifications.notify(
            session, event=event, application=application, reason=reason, actor=actor
        )
    return application
