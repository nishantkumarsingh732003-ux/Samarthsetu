"""Phase 0 schema guarantees.

These run without a database: they assert against SQLAlchemy metadata and the Alembic
script directory, so CI does not need Postgres to catch a schema regression.
"""

from pathlib import Path

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.models import Base

API_ROOT = Path(__file__).resolve().parents[1]

EXPECTED_TABLES = {
    "citizens",
    "consents",
    "citizen_profiles",
    "schemes",
    "scheme_rules",
    "channel_partners",
    "partner_scheme_authorisations",
    "applications",
    "documents",
    "audit_log",
    "match_runs",
    # Phase 6: console logins. The citizen surface still needs no account.
    "users",
}


def test_all_expected_tables_are_registered() -> None:
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_partner_geo_has_a_spatial_index() -> None:
    """Routing sorts 120+ partners by distance on every request."""
    index = next(
        i for i in Base.metadata.tables["channel_partners"].indexes
        if i.name == "ix_channel_partners_geom"
    )
    assert index.dialect_options["postgresql"]["using"] == "gist"


def test_service_districts_has_a_gin_index() -> None:
    """`:district = ANY(service_districts)` is the hard filter in partner routing."""
    index = next(
        i for i in Base.metadata.tables["partner_scheme_authorisations"].indexes
        if i.name == "ix_partner_scheme_authorisations_service_districts"
    )
    assert index.dialect_options["postgresql"]["using"] == "gin"


@pytest.mark.parametrize("column", ["gov_id_last4", "phone_last4"])
def test_identity_columns_cannot_hold_more_than_four_digits(column: str) -> None:
    """DPDP rule 4: a full government ID must be unstorable, not merely unstored."""
    col = Base.metadata.tables["citizens"].columns[column]
    assert col.type.length == 4

    checks = [
        c.sqltext.text
        for c in Base.metadata.tables["citizens"].constraints
        if hasattr(c, "sqltext") and column in str(c.sqltext)
    ]
    assert any("[0-9]{4}" in text for text in checks), f"no 4-digit CHECK on {column}"


def test_schemes_carry_provenance_columns() -> None:
    """CLAUDE.md rule 2: no scheme figure without a source."""
    columns = set(Base.metadata.tables["schemes"].columns.keys())
    assert {"source_url", "circular_ref", "effective_from", "last_verified_on"} <= columns
    assert "needs_verification" in columns


def test_match_runs_records_engine_version() -> None:
    """Reproducibility: a verdict must be traceable to the engine that produced it."""
    columns = Base.metadata.tables["match_runs"].columns
    assert not columns["engine_version"].nullable
    assert not columns["input_snapshot"].nullable
    assert not columns["results"].nullable


def test_alembic_has_exactly_one_head() -> None:
    """A branched history means `alembic upgrade head` is ambiguous."""
    config = Config(str(API_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(API_ROOT / "alembic"))
    heads = ScriptDirectory.from_config(config).get_heads()
    assert len(heads) == 1, f"expected one head, found {heads}"
