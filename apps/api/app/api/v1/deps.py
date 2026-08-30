"""Shared FastAPI dependencies.

Using `Annotated` aliases rather than `Depends()` in argument defaults keeps route
signatures readable and avoids the function-call-in-default pattern that linters flag.

The role dependencies below are the only authorisation in the system, and they are
deliberately blunt: a route either requires a role or it does not. Anything finer —
which partner may see which application — is expressed as a **filter inside the query**
rather than a check beside it, so forgetting the check cannot widen the result set.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidToken, decode_access_token
from app.db.session import get_session
from app.models import User
from app.models.enums import UserRole

SessionDep = Annotated[AsyncSession, Depends(get_session)]

UNAUTHENTICATED = HTTPException(
    status.HTTP_401_UNAUTHORIZED,
    "Not signed in.",
    headers={"WWW-Authenticate": "Bearer"},
)


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    scheme, _, token = header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UNAUTHENTICATED
    return token


async def current_user(request: Request, session: SessionDep) -> User:
    """The signed-in user, or 401.

    The role is re-read from the database rather than trusted from the token. The token
    carries a role so a gateway could authorise cheaply, but this service has the
    database in hand, and a user deactivated five minutes ago should not still be able
    to act for the remaining fifty-five minutes of their token's life.
    """
    payload = None
    try:
        payload = decode_access_token(_bearer_token(request))
    except InvalidToken as exc:
        raise UNAUTHENTICATED from exc

    user = (
        await session.execute(select(User).where(User.email == payload.get("sub")))
    ).scalar_one_or_none()
    if user is None or not user.is_active:
        raise UNAUTHENTICATED
    return user


CurrentUser = Annotated[User, Depends(current_user)]


def require_role(*roles: UserRole):
    """A dependency that admits only the given roles."""

    async def guard(user: CurrentUser) -> User:
        if user.role not in roles:
            # 403, not 404: the caller is authenticated and this is a real endpoint.
            # Hiding its existence from a signed-in user buys nothing and confuses them.
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                f"This needs the {' or '.join(str(r) for r in roles)} role.",
            )
        return user

    return guard


AdminUser = Annotated[User, Depends(require_role(UserRole.ADMIN))]
PartnerUser = Annotated[User, Depends(require_role(UserRole.PARTNER))]
ConsoleUser = Annotated[User, Depends(require_role(UserRole.PARTNER, UserRole.ADMIN))]
