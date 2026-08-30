"""Password hashing and JWT issuance.

Deliberately small. The problem statement is about routing citizens to the right
Channel Partner, not about identity infrastructure, and a hand-rolled OAuth flow would
be a liability rather than a feature. Production integrates with NIC / Parichay SSO;
this is the seam where that swap happens.

**bcrypt is used directly rather than through passlib.** passlib 1.7.4 raises
`ValueError: password cannot be longer than 72 bytes` on import against bcrypt >= 4.1
because it probes the backend with a 72-byte test vector. Pinning passlib's dependency
backwards to keep a wrapper we barely use is the wrong trade; `bcrypt` is a four-function
API and we use two of them.

The 72-byte limit is bcrypt's own, not passlib's, so it still applies: a longer password
is rejected at registration rather than silently truncated, because silent truncation
means two different passwords open the same account.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

ALGORITHM = "HS256"

# bcrypt hashes at most the first 72 bytes of a password.
MAX_PASSWORD_BYTES = 72


class PasswordTooLong(ValueError):
    """Longer than bcrypt can hash. Rejected rather than truncated."""


class InvalidToken(ValueError):
    """The token is missing, malformed, expired, or signed with another key."""


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise PasswordTooLong(
            f"Password is {len(encoded)} bytes; bcrypt hashes at most {MAX_PASSWORD_BYTES}. "
            "Truncating it silently would let two different passwords open one account."
        )
    return bcrypt.hashpw(encoded, bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Constant-time comparison. Returns False for a malformed hash rather than raising."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    subject: str,
    role: str,
    extra: dict[str, Any] | None = None,
    expires_minutes: int | None = None,
) -> str:
    """Sign a token carrying the subject, the role, and nothing sensitive.

    The role is *in* the token, so a route can authorise without a database round trip,
    and a role change therefore takes effect only when the token is reissued. At a
    one-hour expiry that is an acceptable window; it is written down here so nobody
    later assumes revocation is instant.
    """
    minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        # The reason is deliberately not surfaced to the caller: "expired" and "bad
        # signature" are different facts, and only one of them is the client's business.
        raise InvalidToken("Could not validate credentials.") from exc
