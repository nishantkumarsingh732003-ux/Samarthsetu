"""Creating a citizen record, with consent first and the ID masked on the way in.

The ordering here is the point. A `consents` row is written **before** the citizen, and
`citizens.consent_id` is NOT NULL, so there is no code path that stores citizen data
without a consent record to point at — the database refuses it rather than trusting this
function to have remembered.

The government ID is reduced to `last4` plus a salted hash inside this module. The full
value exists as a local variable and nowhere else; it is never assigned to a model
field, never logged, and never returned.
"""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Citizen, Consent
from app.models.enums import GovIdType
from app.services import audit, redaction


class ConsentRequired(PermissionError):
    """No explicit grant, so nothing may be stored."""


def _last4(value: str) -> str | None:
    digits = re.sub(r"\D", "", value)
    return digits[-4:] if len(digits) >= 4 else None


def hash_ip(address: str | None) -> str | None:
    """Consent records prove who granted it without retaining an identifier."""
    if not address:
        return None
    return hashlib.sha256(f"{settings.id_hash_salt}{address}".encode()).hexdigest()


async def record_consent(
    session: AsyncSession,
    *,
    granted: bool,
    purpose: str,
    ip: str | None = None,
) -> Consent:
    if not granted:
        raise ConsentRequired(
            "Consent was not granted, so no personal data can be stored. "
            "Eligibility can still be checked without saving anything."
        )
    consent = Consent(
        purpose=purpose,
        granted_at=datetime.now(UTC),
        policy_version=settings.CONSENT_POLICY_VERSION,
        ip_hash=hash_ip(ip),
    )
    session.add(consent)
    await session.flush()
    return consent


async def create_citizen(
    session: AsyncSession,
    *,
    consent: Consent,
    display_name: str | None = None,
    phone: str | None = None,
    gov_id_type: str | None = None,
    gov_id: str | None = None,
    district: str | None = None,
    state: str | None = None,
    preferred_language: str = "en",
    actor: str = "citizen",
) -> Citizen:
    """Store a citizen. The government ID is masked here, not by the caller.

    If the same ID has been seen before, the existing citizen is returned rather than a
    duplicate created — which is exactly what the salted hash is for. We can recognise a
    returning applicant without ever having held their Aadhaar number.
    """
    id_last4: str | None = None
    id_hash: str | None = None
    resolved_type: GovIdType | None = None

    if gov_id:
        id_last4 = _last4(gov_id)
        if id_last4 is None:
            raise ValueError("The ID number does not contain four digits to keep.")
        id_hash = redaction.salted_hash(gov_id, settings.id_hash_salt)
        resolved_type = GovIdType(gov_id_type) if gov_id_type else GovIdType.OTHER

        existing = (
            await session.execute(select(Citizen).where(Citizen.gov_id_hash == id_hash))
        ).scalar_one_or_none()
        if existing is not None:
            await audit.record(
                session,
                actor=actor,
                action="CITIZEN_RECOGNISED",
                entity="citizen",
                entity_id=str(existing.id),
                meta={"gov_id_last4": id_last4, "matched_on": "salted_hash"},
            )
            return existing

    citizen = Citizen(
        gov_id_type=resolved_type,
        gov_id_last4=id_last4,
        gov_id_hash=id_hash,
        display_name=display_name,
        phone_last4=_last4(phone) if phone else None,
        consent_id=consent.id,
        preferred_language=preferred_language,
        district=district,
        state=state,
    )
    session.add(citizen)
    await session.flush()

    await audit.record(
        session,
        actor=actor,
        action="CITIZEN_CREATED",
        entity="citizen",
        entity_id=str(citizen.id),
        # Note what is absent as much as what is present: no name, no full ID.
        meta={
            "consent_id": str(consent.id),
            "policy_version": settings.CONSENT_POLICY_VERSION,
            "gov_id_type": str(resolved_type) if resolved_type else None,
            "gov_id_last4": id_last4,
            "district": district,
            "state": state,
        },
    )
    return citizen


async def get(session: AsyncSession, citizen_id: uuid.UUID) -> Citizen | None:
    return (
        await session.execute(select(Citizen).where(Citizen.id == citizen_id))
    ).scalar_one_or_none()
