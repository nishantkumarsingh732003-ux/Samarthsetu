"""Seed one login per role.

Demo credentials, and they are demo credentials on purpose: the passwords are printed
by the seeder and written in the README, because a hackathon judge needs to sign in
within ten seconds of opening the laptop.

`SEED_PASSWORD` overrides them for anything resembling a real environment. If the
default is still in place and `ENVIRONMENT` is not `development`, seeding refuses —
shipping `partner123` to a server is a mistake that should require deleting a guard
rather than forgetting one.
"""

from __future__ import annotations

import os

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models import ChannelPartner, User
from app.models.enums import UserRole

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


async def seed(session: AsyncSession) -> int:
    password = os.environ.get("SEED_PASSWORD", "").strip() or DEFAULT_PASSWORD

    if password == DEFAULT_PASSWORD and settings.ENVIRONMENT != "development":
        raise UnsafeSeed(
            f"ENVIRONMENT is {settings.ENVIRONMENT!r} and SEED_PASSWORD is unset, so this "
            "would create logins with the published demo password. Set SEED_PASSWORD."
        )

    created = 0
    for account in ACCOUNTS:
        existing = (
            await session.execute(select(User).where(User.email == account["email"]))
        ).scalar_one_or_none()
        if existing is not None:
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
    print(f"  users: {created} created, {total} total")
    if created:
        shown = password if password == DEFAULT_PASSWORD else "<from SEED_PASSWORD>"
        for account in ACCOUNTS:
            print(f"    {account['role']:<8} {account['email']}  /  {shown}")
    return created
