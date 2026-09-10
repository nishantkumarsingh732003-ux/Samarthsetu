"""The database URL is normalised to asyncpg, whatever the platform hands over.

This exists because a deploy died on it. Render's `fromDatabase: connectionString`
injects a plain `postgresql://…` with no driver, SQLAlchemy defaults the `postgresql`
dialect to psycopg2, and the image installs only asyncpg — so `alembic upgrade head` in
the entrypoint failed with `ModuleNotFoundError: No module named 'psycopg2'` before the
app could start. Nothing in the test suite caught it, because every local path already
sets `+asyncpg` in compose and in the default.

The application is async end to end. The driver is not a per-environment preference; it
is the only one that can work, so it is forced rather than configured.
"""

from __future__ import annotations

import pytest

from app.core.config import Settings


def url_for(value: str) -> str:
    return Settings(DATABASE_URL=value).DATABASE_URL


class TestDriverIsForced:
    def test_render_style_url_gains_the_async_driver(self) -> None:
        # Exactly what `fromDatabase: connectionString` produced on the failed deploy.
        assert url_for("postgresql://setu:pw@dpg-abc123-a/setu_db") == (
            "postgresql+asyncpg://setu:pw@dpg-abc123-a/setu_db"
        )

    def test_legacy_postgres_scheme_is_upgraded_too(self) -> None:
        # SQLAlchemy 2 rejects `postgres://` outright; Heroku-descended platforms still
        # emit it, so it is normalised rather than left to raise.
        assert url_for("postgres://u:p@host:5432/db") == "postgresql+asyncpg://u:p@host:5432/db"

    def test_a_url_that_already_names_asyncpg_is_left_alone(self) -> None:
        original = "postgresql+asyncpg://saarthi:saarthi@localhost:5432/saarthi"
        assert url_for(original) == original

    def test_the_default_is_already_correct(self) -> None:
        assert Settings().DATABASE_URL.startswith("postgresql+asyncpg://")


class TestTlsParameter:
    """`sslmode` is libpq's spelling; asyncpg calls it `ssl`.

    SQLAlchemy passes query parameters to the driver as keyword arguments, so `sslmode`
    would reach `asyncpg.connect(sslmode=...)` and raise. It is renamed rather than
    dropped: every provider that appends it also *requires* TLS, so removing it would
    trade a clear error for a connection the server refuses.
    """

    def test_sslmode_is_renamed_not_dropped(self) -> None:
        assert url_for("postgresql://u:p@host/db?sslmode=require") == (
            "postgresql+asyncpg://u:p@host/db?ssl=require"
        )

    def test_the_value_is_carried_across(self) -> None:
        # A deployment asking for verify-full keeps asking for it.
        assert url_for("postgresql://u:p@host/db?sslmode=verify-full").endswith("ssl=verify-full")

    def test_other_query_parameters_survive(self) -> None:
        out = url_for("postgresql://u:p@host/db?sslmode=require&application_name=setu")
        assert out.startswith("postgresql+asyncpg://u:p@host/db?")
        assert "application_name=setu" in out
        assert "ssl=require" in out
        assert "sslmode" not in out

    def test_an_explicit_ssl_parameter_wins(self) -> None:
        out = url_for("postgresql://u:p@host/db?ssl=verify-full&sslmode=require")
        assert "ssl=verify-full" in out
        assert "sslmode" not in out
        assert out.count("ssl=") == 1

    def test_asyncpg_actually_accepts_what_we_produce(self) -> None:
        """The point of the rename: SQLAlchemy must hand the driver a keyword it knows."""
        from sqlalchemy.ext.asyncio import create_async_engine

        engine = create_async_engine(url_for("postgresql://u:p@host/db?sslmode=require"))
        _, connect_args = engine.dialect.create_connect_args(engine.url)
        assert connect_args["ssl"] == "require"
        assert "sslmode" not in connect_args


class TestCredentialsSurvive:
    @pytest.mark.parametrize(
        "value",
        [
            "postgresql://user:p%40ss%2Fword@host:5432/db",
            "postgresql://user@host/db",
            "postgresql://user:pw@host:5432/db",
        ],
    )
    def test_the_rest_of_the_url_is_untouched(self, value: str) -> None:
        # Only the scheme changes. A rewritten password would fail authentication in a way
        # that looks like a wrong secret rather than a parsing bug.
        assert url_for(value) == value.replace("postgresql://", "postgresql+asyncpg://", 1)


def test_alembic_offline_can_still_strip_the_driver() -> None:
    """`alembic/env.py` renders offline SQL by removing `+asyncpg`. That has to keep
    yielding a URL SQLAlchemy can parse after normalisation."""
    normalised = url_for("postgresql://u:p@host/db")
    assert normalised.replace("+asyncpg", "") == "postgresql://u:p@host/db"
