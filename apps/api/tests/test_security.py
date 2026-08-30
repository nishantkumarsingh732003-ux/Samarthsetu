"""Password hashing and token issuance.

The interesting cases are the ones where a plausible implementation is silently wrong:
a password longer than bcrypt can hash, a token signed with another key, an expired
token that still parses. Each of those fails open if nobody wrote it down.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    MAX_PASSWORD_BYTES,
    InvalidToken,
    PasswordTooLong,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_a_password_round_trips() -> None:
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed)
    assert not verify_password("Correct horse battery staple", hashed)


def test_the_hash_is_salted_so_two_identical_passwords_differ() -> None:
    assert hash_password("same") != hash_password("same")


def test_the_plaintext_never_appears_in_the_hash() -> None:
    assert "hunter2" not in hash_password("hunter2")


def test_an_over_long_password_is_refused_not_truncated() -> None:
    """bcrypt hashes 72 bytes. Silently truncating means two passwords open one account."""
    with pytest.raises(PasswordTooLong):
        hash_password("a" * (MAX_PASSWORD_BYTES + 1))


def test_a_multibyte_password_is_measured_in_bytes_not_characters() -> None:
    """'क' is three bytes. A character-count check would let 72 of them through."""
    too_long = "क" * 25  # 75 bytes
    assert len(too_long) < MAX_PASSWORD_BYTES
    with pytest.raises(PasswordTooLong):
        hash_password(too_long)


def test_a_password_of_exactly_the_limit_is_accepted() -> None:
    at_limit = "a" * MAX_PASSWORD_BYTES
    assert verify_password(at_limit, hash_password(at_limit))


def test_verifying_against_a_malformed_hash_is_false_not_an_exception() -> None:
    """A corrupted row must fail the login, not 500 the endpoint."""
    assert verify_password("anything", "not-a-bcrypt-hash") is False
    assert verify_password("anything", "") is False


# --- tokens ------------------------------------------------------------------------


def test_a_token_carries_the_subject_and_role() -> None:
    payload = decode_access_token(create_access_token("a@b.in", "ADMIN"))
    assert payload["sub"] == "a@b.in"
    assert payload["role"] == "ADMIN"


def test_a_token_signed_with_another_key_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": "a@b.in", "role": "ADMIN", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "not-our-secret",
        algorithm=ALGORITHM,
    )
    with pytest.raises(InvalidToken):
        decode_access_token(forged)


def test_an_expired_token_is_rejected() -> None:
    stale = create_access_token("a@b.in", "ADMIN", expires_minutes=-1)
    with pytest.raises(InvalidToken):
        decode_access_token(stale)


def test_an_unsigned_token_is_rejected() -> None:
    """`alg: none` is the classic JWT bypass and must not parse."""
    unsigned = jwt.encode({"sub": "a@b.in", "role": "ADMIN"}, "", algorithm="HS256").rsplit(
        ".", 1
    )[0] + "."
    with pytest.raises(InvalidToken):
        decode_access_token(unsigned)


def test_garbage_is_rejected_rather_than_raising_something_unexpected() -> None:
    for value in ("", "abc", "a.b.c", "Bearer x"):
        with pytest.raises(InvalidToken):
            decode_access_token(value)


def test_the_failure_message_does_not_say_why() -> None:
    """Expired and forged are different facts; only one of them is the client's."""
    stale = create_access_token("a@b.in", "ADMIN", expires_minutes=-1)
    with pytest.raises(InvalidToken) as caught:
        decode_access_token(stale)
    assert "expire" not in str(caught.value).lower()


def test_a_token_is_signed_with_the_configured_secret() -> None:
    token = create_access_token("a@b.in", "PARTNER")
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["role"] == "PARTNER"
