"""Logging, tracing, error shape, and rate-limit banding.

These are the parts nobody exercises until an incident, which is precisely why they are
tested here rather than trusted. A JSON formatter that raises on an odd `extra` swallows
the very message you needed; an error handler that leaks a traceback hands an attacker a
map of the codebase.
"""

from __future__ import annotations

import json
import logging

import pytest

from app.core import middleware
from app.core.config import settings
from app.core.logging import JsonFormatter, current_request_id, new_request_id, request_id_var


def _record(msg: str = "hello", **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("test", logging.INFO, __file__, 1, msg, (), None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


# --- structured logging ----------------------------------------------------------------


def test_a_log_line_is_one_json_object() -> None:
    line = JsonFormatter().format(_record())
    payload = json.loads(line)
    assert payload["msg"] == "hello"
    assert payload["level"] == "INFO"
    assert "\n" not in line, "a multi-line log record breaks line-oriented tooling"


def test_extra_fields_become_top_level_keys() -> None:
    """`extra={"duration_ms": 12}` must be greppable as a field, not buried in prose."""
    payload = json.loads(JsonFormatter().format(_record(duration_ms=12.5, path="/x")))
    assert payload["duration_ms"] == 12.5
    assert payload["path"] == "/x"


def test_the_request_id_is_stamped_from_the_context() -> None:
    token = request_id_var.set("abc123")
    try:
        payload = json.loads(JsonFormatter().format(_record()))
        assert payload["request_id"] == "abc123"
    finally:
        request_id_var.reset(token)


def test_an_unserialisable_extra_still_produces_a_line() -> None:
    """A logger that raises loses the message you were trying to log — the worst case."""

    class Awkward:
        def __repr__(self) -> str:
            raise RuntimeError("even repr fails")

    line = JsonFormatter().format(_record(thing=Awkward()))
    payload = json.loads(line)
    assert payload["msg"] == "hello"
    assert payload["request_id"]


def test_an_exception_is_captured_as_a_field() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = _record("failed")
        record.exc_info = sys.exc_info()
        payload = json.loads(JsonFormatter().format(record))
    assert "boom" in payload["exc"]


def test_request_ids_are_unique_and_short_enough_to_read_aloud() -> None:
    ids = {new_request_id() for _ in range(500)}
    assert len(ids) == 500
    assert all(len(value) == 16 for value in ids)


def test_the_default_request_id_is_a_placeholder_not_an_empty_string() -> None:
    """Outside a request there is no ID, and a blank field reads as a bug."""
    assert current_request_id() == "-"


# --- rate limit banding ------------------------------------------------------------------


def test_the_conversation_endpoint_is_metered_harder_than_the_rest() -> None:
    """It costs a model call; a browse of the checklist does not."""
    _, conversation = middleware._limit_for("/api/v1/conversation/turn")
    _, default = middleware._limit_for("/api/v1/documents/checklist")
    assert conversation < default


def test_login_is_metered_hardest() -> None:
    """The only endpoint worth brute-forcing."""
    _, login = middleware._limit_for("/api/v1/auth/login")
    _, conversation = middleware._limit_for("/api/v1/conversation/turn")
    assert login < conversation


def test_the_feature_phone_channel_shares_the_conversation_budget() -> None:
    """Same orchestrator, same cost, so the same allowance."""
    assert middleware._limit_for("/api/v1/webhook/whatsapp") == middleware._limit_for(
        "/api/v1/conversation/turn"
    )


def test_paths_are_grouped_so_varying_the_url_does_not_reset_the_budget() -> None:
    a, _ = middleware._limit_for("/api/v1/applications/SETU-2026-MH-000001")
    b, _ = middleware._limit_for("/api/v1/applications/SETU-2026-MH-000002")
    assert a == b == "default"


@pytest.mark.parametrize("path", ["/health", "/docs", "/openapi.json"])
def test_health_and_docs_are_never_rate_limited(path: str) -> None:
    """An orchestrator polling health must not be able to take the service out."""
    assert path in middleware.EXEMPT_PATHS


def test_the_limits_are_generous_enough_for_a_real_citizen() -> None:
    """Someone tapping through six screens on 2G, retrying twice, must not be blocked."""
    assert settings.RATE_LIMIT_DEFAULT >= 60
    assert settings.RATE_LIMIT_CONVERSATION >= 20
