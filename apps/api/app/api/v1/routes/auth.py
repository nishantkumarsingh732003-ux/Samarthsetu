"""Sign-in for the partner console and the MoSJE dashboard.

Deliberately minimal: email, password, a signed token, three roles. No OAuth provider,
no email verification, no refresh-token rotation. Production integrates with NIC /
Parichay SSO and this endpoint is the seam where that swap happens — the rest of the
API only ever asks `deps.current_user` who is calling.

The citizen journey has no login at all. An application is tracked by its reference
number, because requiring an account to find out which scheme fits you is exactly the
barrier this project exists to remove.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, SessionDep
from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models import ChannelPartner, User
from app.schemas.console import LoginRequest, LoginResponse, UserOut
from app.services import audit

router = APIRouter()

# Wrong email and wrong password return this same message on purpose: a login form that
# distinguishes them tells an attacker which addresses are registered.
BAD_CREDENTIALS = HTTPException(
    status.HTTP_401_UNAUTHORIZED, "That email and password do not match."
)

# A genuine bcrypt hash of a random value nobody holds, used only so that an unknown
# email costs the same ~200ms as a known one. A literal that is not valid bcrypt would
# fail fast and reintroduce exactly the timing oracle it is meant to remove.
_DUMMY_HASH = "$2b$12$iAqKiJmggGQChuy2Vf0Q7eMDlycX7PI7b7MPPCTUNIpZlnn7/YBW."


async def _as_out(session: AsyncSession, user: User) -> UserOut:
    partner_name = None
    if user.partner_id:
        partner_name = (
            await session.execute(
                select(ChannelPartner.name).where(ChannelPartner.id == user.partner_id)
            )
        ).scalar_one_or_none()
    return UserOut(
        id=str(user.id),
        email=user.email,
        display_name=user.display_name,
        role=str(user.role),
        partner_id=str(user.partner_id) if user.partner_id else None,
        partner_name=partner_name,
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Sign in to a console",
    description="Returns a bearer token carrying the role. Citizens do not need one.",
)
async def login(
    payload: LoginRequest,
    request: Request,
    session: SessionDep,
) -> LoginResponse:
    user = (
        await session.execute(select(User).where(User.email == payload.email.strip().lower()))
    ).scalar_one_or_none()

    # Verify against a dummy hash when the user does not exist, so a missing account and
    # a wrong password take the same time. Without this, response timing is an oracle
    # for which addresses are registered.
    hashed = user.password_hash if user else _DUMMY_HASH
    matched = verify_password(payload.password, hashed)

    if user is None or not matched or not user.is_active:
        await audit.record(
            session,
            actor=request.client.host if request.client else "unknown",
            action="LOGIN_FAILED",
            entity="user",
            entity_id=None,
            # The attempted address is not recorded: a failed login often means someone
            # typed their password into the email box.
            meta={"reason": "invalid_credentials"},
        )
        await session.commit()
        raise BAD_CREDENTIALS

    token = create_access_token(
        subject=user.email,
        role=str(user.role),
        extra={"partner_id": str(user.partner_id) if user.partner_id else None},
    )

    await audit.record(
        session,
        actor=user.email,
        action="LOGIN_SUCCEEDED",
        entity="user",
        entity_id=str(user.id),
        meta={"role": str(user.role)},
    )
    out = await _as_out(session, user)
    await session.commit()

    return LoginResponse(
        access_token=token,
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=out,
    )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Who the current token belongs to",
)
async def me(user: CurrentUser, session: SessionDep) -> UserOut:
    return await _as_out(session, user)
