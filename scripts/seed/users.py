"""Seed one login per role.

Demo credentials, and they are demo credentials on purpose: the passwords are printed
by the seeder and written in the README, because a hackathon judge needs to sign in
within ten seconds of opening the laptop.

`SEED_PASSWORD` overrides them for anything resembling a real environment. If the
default is still in place and `ENVIRONMENT` is not `development`, seeding refuses —
shipping `partner123` to a server is a mistake that should require deleting a guard
rather than forgetting one.

The citizen login is different in kind from the other two. A citizen account stores
personal data, so it needs a `consents` row and a `citizens` row behind it — and those
go through `services.citizen_accounts`, the same path a real signup takes, rather than
being inserted directly here. A seeder that wrote a citizen without a consent record
would be demonstrating the exact thing the schema is built to prevent.
"""

from __future__ import annotations

import os

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import ChannelPartner, CitizenProfile, User
from app.models.enums import UserRole
from app.services import citizen_accounts, citizens

DEFAULT_PASSWORD = "setu-demo-2026"

ACCOUNTS = [
    {
        "email": "admin@setu.gov.in",
        "display_name": "MoSJE Analyst",
        "role": UserRole.ADMIN,
        "partner": None,
    },
    {
        "email": "partner@setu.gov.in",
        "display_name": "Branch Officer",
        "role": UserRole.PARTNER,
        # Resolved to a real partner below — the one the demo journey routes to.
        "partner": "Fusion Micro Finance — Nagpur Service Centre",
    },
    {
        "email": "citizen@setu.gov.in",
        "display_name": "Demo Citizen",
        "role": UserRole.CITIZEN,
        "partner": None,
    },
]


class UnsafeSeed(RuntimeError):
    """The default demo password would have been written outside development."""


async def attach_citizen_record(session: AsyncSession, user: User) -> bool:
    """Give a citizen login the consent record and profile it needs, if it has none.

    Two callers, for two different reasons:

    - this seeder, so a database seeded by an older build is repaired rather than left
      with a citizen login that 403s on every citizen route;
    - `demo.py`, because resetting the demo world truncates `citizens`, which takes the
      link with it.

    Goes through `services.citizens` rather than inserting directly, so the `consents`
    row is written first and `citizens.consent_id` is satisfied the same way a real
    signup satisfies it.
    """
    if user.role is not UserRole.CITIZEN or user.citizen_id is not None:
        return False

    consent = await citizens.record_consent(
        session,
        granted=True,
        purpose=citizen_accounts.SIGNUP_CONSENT_PURPOSE,
        ip=None,
    )
    citizen = await citizens.create_citizen(
        session,
        consent=consent,
        display_name=user.display_name,
        actor=user.email,
    )
    session.add(CitizenProfile(citizen_id=citizen.id))
    user.citizen_id = citizen.id
    await session.flush()
    return True


async def repair_citizen_logins(session: AsyncSession) -> int:
    """Re-attach every citizen login that has lost its citizen record."""
    users = (
        (await session.execute(select(User).where(User.role == UserRole.CITIZEN)))
        .scalars()
        .all()
    )
    return sum([await attach_citizen_record(session, user) for user in users])


async def seed(session: AsyncSession) -> int:
    password = os.environ.get("SEED_PASSWORD", "").strip() or DEFAULT_PASSWORD

    if password == DEFAULT_PASSWORD and settings.ENVIRONMENT != "development":
        raise UnsafeSeed(
            f"ENVIRONMENT is {settings.ENVIRONMENT!r} and SEED_PASSWORD is unset, so this "
            "would create logins with the published demo password. Set SEED_PASSWORD."
        )

    created = 0
    repaired = 0
    for account in ACCOUNTS:
        existing = (
            await session.execute(select(User).where(User.email == account["email"]))
        ).scalar_one_or_none()
        if existing is not None:
            # A citizen login whose citizen record is missing — seeded by an older build,
            # or cleared by `demo.py`'s reset — 403s on every citizen route. Repair it in
            # place rather than skipping, so `make seed` fixes it instead of quietly
            # leaving it broken.
            if await attach_citizen_record(session, existing):
                repaired += 1
            continue

        if account["role"] is UserRole.CITIZEN:
            # Through the real signup path, so the consent record exists and the
            # database's NOT NULL on `citizens.consent_id` is satisfied the same way it
            # is for a citizen who signs up on the website.
            await citizen_accounts.create_account(
                session,
                email=account["email"],
                password=password,
                display_name=account["display_name"],
                ip=None,
            )
            created += 1
            continue

        partner_id = None
        if account["partner"]:
            partner_id = (
                await session.execute(
                    select(ChannelPartner.id).where(ChannelPartner.name == account["partner"])
                )
            ).scalar_one_or_none()
            if partner_id is None:
                # Fall back to any NBFC-MFI in Nagpur, then to any partner at all, so a
                # reseed with different synthetic data still produces a usable login.
                partner_id = (
                    await session.execute(
                        select(ChannelPartner.id)
                        .where(ChannelPartner.district == "Nagpur")
                        .order_by(ChannelPartner.name)
                        .limit(1)
                    )
                ).scalar_one_or_none()
            if partner_id is None:
                partner_id = (
                    await session.execute(select(ChannelPartner.id).limit(1))
                ).scalar_one_or_none()
            if partner_id is None:
                raise UnsafeSeed(
                    "No Channel Partners exist, so a partner login cannot be created. "
                    "Seed partners first."
                )

        session.add(
            User(
                email=account["email"],
                password_hash=hash_password(password),
                display_name=account["display_name"],
                role=account["role"],
                partner_id=partner_id,
            )
        )
        created += 1

    await session.flush()
    total = (await session.execute(select(func.count()).select_from(User))).scalar_one()
    repair_note = f", {repaired} repaired" if repaired else ""
    print(f"  users: {created} created{repair_note}, {total} total")
    if created:
        shown = password if password == DEFAULT_PASSWORD else "<from SEED_PASSWORD>"
        for account in ACCOUNTS:
            print(f"    {account['role']:<8} {account['email']}  /  {shown}")
    return created
