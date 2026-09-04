"""The optional citizen account: signup, a stored profile, and its own applications.

Everything here is a convenience layer over surfaces that already work without a login.
`GET /citizen/matches` runs the identical deterministic engine that `POST /match` runs;
the only difference is that the profile is read from a table instead of a request body.
A signed-in citizen never gets a different verdict from an anonymous one with the same
facts, and the shared `MatchResultOut` shape is what keeps that honest.

Sign-in itself is `POST /auth/login`, the same endpoint the consoles use. One password
path, one place to swap in NIC / Parichay SSO later, one endpoint to meter hardest.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date
from typing import cast

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import CitizenUser, SessionDep
from app.core import cache
from app.core.config import settings
from app.core.security import PasswordTooLong, create_access_token
from app.models import Application, ChannelPartner, Citizen, CitizenProfile, Scheme, User
from app.schemas.citizen import (
    CitizenAccountOut,
    CitizenApplicationSummary,
    CitizenMatchResponse,
    CitizenProfileIn,
    CitizenProfileOut,
    SignupRequest,
    SignupResponse,
)
from app.services import audit, citizen_accounts, matching

router = APIRouter()

# A matched profile is cached so that opening the dashboard four times does not write
# four `match_runs` rows for one unchanged set of answers. The key carries the engine
# version, so publishing new rules invalidates every citizen's cached verdict at once —
# which is the correct behaviour and the reason the version is in the key rather than a
# TTL being relied on to expire it eventually.
MATCH_CACHE_TTL_SECONDS = 300


def _match_cache_key(citizen_id: str, engine_profile: dict, language: str) -> str:
    from setu_rules import ENGINE_VERSION, rules_digest

    fingerprint = hashlib.sha256(
        json.dumps(engine_profile, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]
    return (
        f"setu:citizen-match:{ENGINE_VERSION}:{rules_digest()[:12]}"
        f":{citizen_id}:{language}:{fingerprint}"
    )


def _profile_out(citizen: Citizen, profile: CitizenProfile) -> CitizenProfileOut:
    def number(value) -> float | None:
        return float(value) if value is not None else None

    return CitizenProfileOut(
        display_name=citizen.display_name,
        preferred_language=citizen.preferred_language,
        district=citizen.district,
        state=citizen.state,
        city=citizen.city,
        pincode=citizen.pincode,
        category=str(profile.category) if profile.category else None,
        sub_category=profile.sub_category,
        gender=str(profile.gender) if profile.gender else None,
        age=profile.age,
        annual_family_income=number(profile.annual_family_income),
        occupation_type=profile.occupation_type,
        education_level=profile.education_level,
        existing_loans=number(profile.existing_loans),
        project_cost=number(profile.project_cost),
        project_sector=profile.project_sector,
        is_pwd=profile.is_pwd,
        is_safai_karamchari=profile.is_safai_karamchari,
        has_caste_certificate=profile.has_caste_certificate,
        admission_confirmed=profile.admission_confirmed,
        # The column is declared `Mapped[object | None]` because SQLAlchemy's Date does
        # not narrow through the mapper. Narrowed here rather than widening the response
        # schema to object, which would lose the shape for every consumer.
        course_start_date=cast("date | None", profile.course_start_date),
        business_name=profile.business_name,
        business_description=profile.business_description,
        business_status=profile.business_status,
        own_contribution=number(profile.own_contribution),
        loan_required=number(profile.loan_required),
        completed=profile.completed_at is not None,
        completion_pct=citizen_accounts.completion(citizen, profile),
        # Shown to the citizen on purpose: this is the exact dictionary the engine is
        # given, so "the business description did not decide this" is checkable rather
        # than merely claimed.
        engine_profile=citizen_accounts.engine_profile(citizen, profile),
    )


def _account_out(user: User, citizen: Citizen, profile: CitizenProfile) -> CitizenAccountOut:
    return CitizenAccountOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=str(user.role),
        citizen_id=str(citizen.id),
        profile=_profile_out(citizen, profile),
    )


async def _load(session: AsyncSession, user: User) -> tuple[Citizen, CitizenProfile]:
    try:
        return await citizen_accounts.load(session, user)
    except citizen_accounts.NotACitizenAccount as exc:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This is a console login. Citizen profiles belong to citizen accounts.",
        ) from exc


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an optional citizen account",
    description=(
        "An account is never required. Checking eligibility, finding a partner and "
        "tracking an application by reference number all work signed out. Signing up "
        "only saves the profile so it does not have to be retyped, and records the "
        "explicit consent that permits storing it."
    ),
)
async def signup(
    payload: SignupRequest,
    request: Request,
    session: SessionDep,
) -> SignupResponse:
    if not payload.consent:
        # Not a 422 about a boolean: this is the DPDP grant, and the message has to say
        # what is still possible without it rather than just refusing.
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "An account stores your profile, so it needs your consent. You can still "
            "check your eligibility and find a partner without one.",
        )

    try:
        user = await citizen_accounts.create_account(
            session,
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
            preferred_language=payload.preferred_language,
            ip=request.client.host if request.client else None,
        )
    except citizen_accounts.EmailAlreadyRegistered as exc:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "That email already has an account. Try signing in instead.",
        ) from exc
    except PasswordTooLong as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    citizen, profile = await citizen_accounts.load(session, user)
    token = create_access_token(subject=user.email, role=str(user.role))
    out = _account_out(user, citizen, profile)
    await session.commit()

    return SignupResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=out,
    )


@router.get(
    "/me",
    response_model=CitizenAccountOut,
    summary="The signed-in citizen and their stored profile",
)
async def me(user: CitizenUser, session: SessionDep) -> CitizenAccountOut:
    citizen, profile = await _load(session, user)
    out = _account_out(user, citizen, profile)
    await session.commit()
    return out


@router.put(
    "/profile",
    response_model=CitizenAccountOut,
    summary="Update the stored profile",
    description=(
        "A partial update: keys that are absent are left alone, and an explicit null "
        "clears a field. Nothing here decides eligibility — the response carries the "
        "`engine_profile` that the rule engine will actually be given."
    ),
)
async def update_profile(
    payload: CitizenProfileIn,
    user: CitizenUser,
    session: SessionDep,
) -> CitizenAccountOut:
    citizen, profile = await _load(session, user)
    try:
        await citizen_accounts.update_profile(
            session,
            citizen=citizen,
            profile=profile,
            patch=payload.patch(),
            completed=payload.completed,
            actor=user.email,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    out = _account_out(user, citizen, profile)
    await session.commit()
    return out


@router.post(
    "/profile/demo",
    response_model=CitizenAccountOut,
    summary="Fill the profile with the demo persona",
    description=(
        "A shortcut through data entry, not through the engine. The persona is written "
        "to the same columns a typed answer would reach, and the verdict that follows "
        "is whatever the published rules say about those numbers."
    ),
)
async def load_demo(user: CitizenUser, session: SessionDep) -> CitizenAccountOut:
    citizen, profile = await _load(session, user)
    await citizen_accounts.load_demo(
        session, citizen=citizen, profile=profile, actor=user.email
    )
    out = _account_out(user, citizen, profile)
    await session.commit()
    return out


@router.get(
    "/matches",
    response_model=CitizenMatchResponse,
    summary="Run the stored profile through the deterministic engine",
    description=(
        "Identical to POST /match in every respect except where the profile came from. "
        "No language model participates in the verdict."
    ),
)
async def matches(
    user: CitizenUser,
    session: SessionDep,
    request: Request,
    language: str = "en",
) -> CitizenMatchResponse:
    citizen, profile = await _load(session, user)
    engine_input = citizen_accounts.engine_profile(citizen, profile)

    key = _match_cache_key(str(citizen.id), engine_input, language)
    payload = await cache.cache_get(key)

    if payload is None:
        try:
            payload = await matching.run_match(
                session,
                profile=engine_input,
                language=language,
                citizen_id=citizen.id,
                actor=user.email,
            )
        except ValueError as exc:
            # A stored profile that the engine rejects means the two contracts have
            # drifted. Say so plainly rather than returning an empty result set.
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
        await session.commit()
        await cache.cache_set(key, payload, ttl=MATCH_CACHE_TTL_SECONDS)
    else:
        # A cached verdict is still a verdict shown to a citizen. Auditing only on a
        # miss would undercount exactly the surface a regulator would ask about.
        await audit.record(
            session,
            actor=user.email,
            action="MATCH_REPLAYED",
            entity="match_run",
            entity_id=payload.get("match_run_id"),
            meta={"engine_version": payload.get("engine_version"), "served_from_cache": True},
        )
        await session.commit()

    results = payload.get("results") or []
    return CitizenMatchResponse(
        match_run_id=payload["match_run_id"],
        engine_version=payload["engine_version"],
        rules_digest=payload["rules_digest"],
        input_snapshot=payload["input_snapshot"],
        results=results,
        next_question=payload.get("next_question"),
        # Derived from the run itself rather than from counting filled-in boxes: the
        # profile is usable exactly when the engine could decide something with it.
        profile_is_usable=any(r.get("verdict") != "NEED_MORE_INFO" for r in results),
    )


@router.get(
    "/applications",
    response_model=list[CitizenApplicationSummary],
    summary="Applications raised by the signed-in citizen, newest first",
)
async def applications(
    user: CitizenUser, session: SessionDep
) -> list[CitizenApplicationSummary]:
    from setu_rules.documents import required_documents

    citizen, _ = await _load(session, user)

    rows = (
        (
            await session.execute(
                select(Application, Scheme, ChannelPartner.name)
                .join(Scheme, Scheme.id == Application.scheme_id)
                .outerjoin(ChannelPartner, ChannelPartner.id == Application.partner_id)
                .options(selectinload(Application.documents))
                .where(Application.citizen_id == citizen.id)
                .order_by(Application.created_at.desc())
            )
        )
        .unique()
        .all()
    )

    out: list[CitizenApplicationSummary] = []
    for application, scheme, partner_name in rows:
        uploaded = {doc.doc_type for doc in application.documents}
        required = required_documents(
            family=str(scheme.family),
            partner_type=None,
            profile={},
            language=citizen.preferred_language,
        )
        out.append(
            CitizenApplicationSummary(
                reference_no=application.reference_no,
                status=str(application.status),
                scheme_code=scheme.code,
                # Official name verbatim, never machine-translated (CLAUDE.md).
                scheme_name=scheme.official_name,
                family=str(scheme.family),
                partner_name=partner_name,
                amount_requested=float(application.amount_requested)
                if application.amount_requested is not None
                else None,
                submitted_at=application.created_at.isoformat()
                if application.created_at
                else None,
                documents_outstanding=sum(1 for doc in required if doc.id not in uploaded),
            )
        )

    await audit.record(
        session,
        actor=user.email,
        action="CITIZEN_APPLICATIONS_LISTED",
        entity="citizen",
        entity_id=str(citizen.id),
        meta={"count": len(out)},
    )
    await session.commit()
    return out
