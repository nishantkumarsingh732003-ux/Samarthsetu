"""Optional citizen accounts: signing in adds persistence, never permission.

The anonymous journey is still the front door. `POST /match` takes a profile in the
request body and decides eligibility for anyone who asks, with no login and no stored
row — that is deliberate, and nothing here weakens it. An account only means the profile
survives the walk home and the citizen sees their own applications instead of holding a
reference number on a scrap of paper.

Two invariants this module exists to hold:

1. **Consent comes first.** Signup writes a `consents` row before the `citizens` row,
   because `citizens.consent_id` is NOT NULL. A signup that somehow skipped consent
   would be refused by the database rather than by a code review.

2. **The engine sees only its own contract.** `engine_profile()` projects the stored
   columns down to `setu_rules.profile.FIELDS` and nothing else. The enterprise columns
   the onboarding collects — business name, own contribution, and so on — are for the
   citizen and the partner to read. If one of them should ever move a verdict, it has to
   be added to the engine contract first, in the open.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models import Citizen, CitizenProfile, User
from app.models.enums import Gender, SocialCategory, UserRole
from app.services import audit, citizens

# The purpose string on the consent record. It says what the citizen agreed to, in the
# words they were shown, so a subject-access request can be answered from the row alone.
SIGNUP_CONSENT_PURPOSE = "Save my eligibility profile and applications to this account"


class EmailAlreadyRegistered(ValueError):
    """That address already has a login."""


class NotACitizenAccount(PermissionError):
    """A console login reached a route that only a citizen account can use."""


# Columns on `CitizenProfile` a citizen may set. Anything outside this set is rejected
# rather than ignored, so a typo in a client is a 422 and not a silently dropped answer.
PROFILE_FIELDS: frozenset[str] = frozenset(
    {
        # read by the rule engine
        "category",
        "sub_category",
        "gender",
        "age",
        "annual_family_income",
        "occupation_type",
        "education_level",
        "existing_loans",
        "project_cost",
        "project_sector",
        "is_pwd",
        "is_safai_karamchari",
        "has_caste_certificate",
        "admission_confirmed",
        "course_start_date",
        # collected by onboarding, not read by the engine
        "business_name",
        "business_description",
        "business_status",
        "own_contribution",
        "loan_required",
        "notes",
    }
)

# Columns on `Citizen` a citizen may set through the same call. Identity fields
# (gov_id_*, consent_id) are deliberately absent: those are set once, by the code that
# holds the consent record, and never patched from a form.
CITIZEN_FIELDS: frozenset[str] = frozenset(
    {"display_name", "preferred_language", "district", "state", "city", "pincode"}
)

_ENUM_COLUMNS: dict[str, type] = {"category": SocialCategory, "gender": Gender}
_DECIMAL_COLUMNS = frozenset(
    {
        "annual_family_income",
        "existing_loans",
        "project_cost",
        "own_contribution",
        "loan_required",
    }
)


async def create_account(
    session: AsyncSession,
    *,
    email: str,
    password: str,
    display_name: str,
    preferred_language: str = "en",
    ip: str | None = None,
) -> User:
    """Register a citizen login, with the consent record written first.

    Raises `EmailAlreadyRegistered` rather than returning the existing user: silently
    signing someone into an account they may not own is worse than a duplicate-email
    error, and the caller has to distinguish the two anyway.
    """
    address = email.strip().lower()
    clash = (await session.execute(select(User.id).where(User.email == address))).first()
    if clash is not None:
        raise EmailAlreadyRegistered(address)

    consent = await citizens.record_consent(
        session, granted=True, purpose=SIGNUP_CONSENT_PURPOSE, ip=ip
    )
    citizen = await citizens.create_citizen(
        session,
        consent=consent,
        display_name=display_name.strip() or None,
        preferred_language=preferred_language,
        actor=address,
    )
    session.add(CitizenProfile(citizen_id=citizen.id))

    user = User(
        email=address,
        password_hash=hash_password(password),
        display_name=display_name.strip() or address,
        role=UserRole.CITIZEN,
        citizen_id=citizen.id,
    )
    session.add(user)
    await session.flush()

    await audit.record(
        session,
        actor=address,
        action="CITIZEN_ACCOUNT_CREATED",
        entity="user",
        entity_id=str(user.id),
        meta={"citizen_id": str(citizen.id), "consent_id": str(consent.id)},
    )
    return user


async def load(session: AsyncSession, user: User) -> tuple[Citizen, CitizenProfile]:
    """The citizen row and profile behind a signed-in account, creating the profile
    lazily if an older account predates it."""
    if user.role is not UserRole.CITIZEN or user.citizen_id is None:
        raise NotACitizenAccount(user.email)

    citizen = (
        await session.execute(select(Citizen).where(Citizen.id == user.citizen_id))
    ).scalar_one()
    profile = (
        await session.execute(
            select(CitizenProfile).where(CitizenProfile.citizen_id == citizen.id)
        )
    ).scalar_one_or_none()
    if profile is None:
        profile = CitizenProfile(citizen_id=citizen.id)
        session.add(profile)
        await session.flush()
    return citizen, profile


def _coerce(field: str, value: Any) -> Any:
    if value is None:
        return None
    if field in _ENUM_COLUMNS:
        return _ENUM_COLUMNS[field](value)
    if field in _DECIMAL_COLUMNS:
        return Decimal(str(value))
    return value


async def update_profile(
    session: AsyncSession,
    *,
    citizen: Citizen,
    profile: CitizenProfile,
    patch: dict[str, Any],
    completed: bool | None = None,
    actor: str = "citizen",
) -> None:
    """Apply a partial update. Absent keys are left alone; explicit nulls clear a field.

    That distinction matters on a 2G connection: a form that failed to submit half its
    fields must not erase the answers a citizen gave last week.
    """
    unknown = set(patch) - PROFILE_FIELDS - CITIZEN_FIELDS
    if unknown:
        raise ValueError(f"Unknown profile field(s): {', '.join(sorted(unknown))}")

    for field, value in patch.items():
        target = citizen if field in CITIZEN_FIELDS else profile
        setattr(target, field, _coerce(field, value))

    if completed:
        profile.completed_at = datetime.now(UTC)
    elif completed is False:
        profile.completed_at = None

    await session.flush()
    await audit.record(
        session,
        actor=actor,
        action="CITIZEN_PROFILE_UPDATED",
        entity="citizen",
        entity_id=str(citizen.id),
        # The field *names* are recorded, never the values. An audit log that copies the
        # profile into itself is a second, less-guarded store of the same personal data.
        meta={"fields": sorted(patch), "completed": bool(profile.completed_at)},
    )


def engine_profile(citizen: Citizen, profile: CitizenProfile) -> dict[str, Any]:
    """Project the stored profile onto the rule engine's contract.

    Only fields the engine declares are included, and only where they have a value —
    a NULL must reach the engine as *absent*, which is what produces NEED_MORE_INFO and
    the next question, rather than as a null that some rule might read as zero.
    """
    from setu_rules import FIELDS

    raw: dict[str, Any] = {
        "category": str(profile.category) if profile.category else None,
        "sub_category": profile.sub_category,
        "gender": str(profile.gender) if profile.gender else None,
        "age": profile.age,
        "annual_family_income": profile.annual_family_income,
        "occupation_type": profile.occupation_type,
        "education_level": profile.education_level,
        "existing_loans": profile.existing_loans,
        "project_cost": profile.project_cost,
        "project_sector": profile.project_sector,
        "is_pwd": profile.is_pwd,
        "is_safai_karamchari": profile.is_safai_karamchari,
        "has_caste_certificate": profile.has_caste_certificate,
        "admission_confirmed": profile.admission_confirmed,
    }

    out: dict[str, Any] = {}
    for field, value in raw.items():
        if value is None or field not in FIELDS:
            continue
        # Numeric columns come back as Decimal, which the engine's arithmetic and the
        # JSON snapshot both need as a plain float.
        out[field] = float(value) if isinstance(value, Decimal) else value
    return out


# Which fields count towards the completion percentage the dashboard shows. Chosen
# because they are what the three scheme families actually turn on — a bar that fills up
# for answering optional questions would be flattering and useless.
COMPLETION_FIELDS: tuple[str, ...] = (
    "category",
    "annual_family_income",
    "project_sector",
    "project_cost",
    "age",
    "gender",
    "has_caste_certificate",
    "district",
    "state",
)


def completion(citizen: Citizen, profile: CitizenProfile) -> int:
    """Percent of the fields that decide eligibility which this profile has answered."""
    answered = 0
    for field in COMPLETION_FIELDS:
        source = citizen if field in CITIZEN_FIELDS else profile
        if getattr(source, field, None) is not None:
            answered += 1
    return round(100 * answered / len(COMPLETION_FIELDS))


# The demo persona. Every value is a plausible answer a real applicant could give, and
# the numbers are chosen to land the profile *inside* the published ceilings (income
# under Rs 5,00,000; a project cost a Term Loan covers and Micro Finance does not) so a
# judge sees the engine distinguish the families rather than agree with everything.
DEMO_CITIZEN: dict[str, Any] = {
    "display_name": "Rahul Kumar",
    "district": "Jaipur",
    "state": "Rajasthan",
    "city": "Jaipur",
    "pincode": "302001",
}
DEMO_PROFILE: dict[str, Any] = {
    "category": "SC",
    "gender": "MALE",
    "age": 31,
    "annual_family_income": 420000,
    "occupation_type": "Tailor",
    "education_level": "Higher Secondary",
    "has_caste_certificate": True,
    "is_pwd": False,
    "is_safai_karamchari": False,
    "existing_loans": 0,
    "project_sector": "MANUFACTURING",
    "project_cost": 1000000,
    "own_contribution": 100000,
    "loan_required": 900000,
    "business_name": "Kumar Tailoring Unit",
    "business_status": "EXISTING",
    "business_description": (
        "A two-machine tailoring unit adding four industrial machines and an overlock, "
        "to take school-uniform orders that currently go to a larger workshop."
    ),
}


async def load_demo(
    session: AsyncSession,
    *,
    citizen: Citizen,
    profile: CitizenProfile,
    actor: str = "citizen",
) -> None:
    """Fill the signed-in account with the demo persona.

    This is a *shortcut through data entry*, not a shortcut through the engine: the
    profile it writes is then matched by the same deterministic run as any other, and
    the verdict is whatever the rules say about these numbers.
    """
    await update_profile(
        session,
        citizen=citizen,
        profile=profile,
        patch={**DEMO_CITIZEN, **DEMO_PROFILE},
        completed=True,
        actor=actor,
    )
    await audit.record(
        session,
        actor=actor,
        action="CITIZEN_DEMO_PROFILE_LOADED",
        entity="citizen",
        entity_id=str(citizen.id),
        meta={"persona": DEMO_CITIZEN["display_name"]},
    )


async def application_ids(session: AsyncSession, citizen_id: uuid.UUID) -> list[uuid.UUID]:
    """Ids of every application this citizen raised, newest first."""
    from app.models import Application

    rows = await session.execute(
        select(Application.id)
        .where(Application.citizen_id == citizen_id)
        .order_by(Application.created_at.desc())
    )
    return list(rows.scalars())
