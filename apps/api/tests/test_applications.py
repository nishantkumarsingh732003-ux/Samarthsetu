"""The application lifecycle, its reference numbers, and consent.

The state machine is tested without a database because it is pure logic and deserves to
be provable in milliseconds. The database-backed guarantees — the NOT NULL consent
foreign key, the 4-digit CHECK on `gov_id_last4` — are proved against a live PostgreSQL
in `scripts/verify_dpdp.py`, because a constraint is only real if the database enforces
it, and an in-memory stub would prove nothing about that.
"""

from __future__ import annotations

import pytest

from app.models import Application
from app.models.enums import ApplicationStatus
from app.services import applications


class FakeSession:
    """Enough of an AsyncSession for the pure-logic paths: collect, do not persist."""

    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        self.added.append(obj)

    async def flush(self) -> None:
        pass


def _application(status: ApplicationStatus) -> Application:
    app = Application()
    app.status = status
    app.reference_no = "SETU-2026-MH-000001"
    app.status_history = []
    return app


# --- reference numbers ------------------------------------------------------------------


def test_a_reference_number_names_the_state_it_was_raised_in() -> None:
    assert applications.state_code("Maharashtra") == "MH"
    assert applications.state_code("West Bengal") == "WB"
    assert applications.state_code("  Tamil Nadu  ") == "TN"


def test_an_unknown_state_is_XX_rather_than_a_guess() -> None:
    assert applications.state_code("Atlantis") == "XX"
    assert applications.state_code(None) == "XX"
    assert applications.state_code("") == "XX"


# --- the state machine --------------------------------------------------------------------


@pytest.mark.parametrize(
    ("start", "target"),
    [
        (ApplicationStatus.SUBMITTED, ApplicationStatus.PARTNER_ACKNOWLEDGED),
        (ApplicationStatus.PARTNER_ACKNOWLEDGED, ApplicationStatus.DOCS_REQUESTED),
        (ApplicationStatus.DOCS_REQUESTED, ApplicationStatus.UNDER_APPRAISAL),
        (ApplicationStatus.UNDER_APPRAISAL, ApplicationStatus.SANCTIONED),
        (ApplicationStatus.SANCTIONED, ApplicationStatus.DISBURSED),
    ],
)
async def test_the_ordinary_path_is_allowed(
    start: ApplicationStatus, target: ApplicationStatus
) -> None:
    app = _application(start)
    await applications.transition(FakeSession(), app, target, actor="partner")
    assert app.status is target


async def test_a_partner_cannot_sanction_what_it_never_acknowledged() -> None:
    """The transition table is a model of the process, not a log of whatever happened."""
    app = _application(ApplicationStatus.SUBMITTED)
    with pytest.raises(applications.IllegalTransition):
        await applications.transition(
            FakeSession(), app, ApplicationStatus.SANCTIONED, actor="partner"
        )
    assert app.status is ApplicationStatus.SUBMITTED, "a refused transition changes nothing"


@pytest.mark.parametrize(
    "terminal",
    [ApplicationStatus.DISBURSED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN],
)
async def test_terminal_states_go_nowhere(terminal: ApplicationStatus) -> None:
    app = _application(terminal)
    with pytest.raises(applications.IllegalTransition):
        await applications.transition(
            FakeSession(), app, ApplicationStatus.UNDER_APPRAISAL, actor="partner"
        )


async def test_a_rejection_is_reachable_from_every_live_state() -> None:
    """A citizen must always be able to be told no, and always be able to walk away."""
    live = [
        ApplicationStatus.SUBMITTED,
        ApplicationStatus.PARTNER_ACKNOWLEDGED,
        ApplicationStatus.DOCS_REQUESTED,
        ApplicationStatus.UNDER_APPRAISAL,
    ]
    for state in live:
        assert ApplicationStatus.REJECTED in applications.ALLOWED_TRANSITIONS[state]
        assert ApplicationStatus.WITHDRAWN in applications.ALLOWED_TRANSITIONS[state]


async def test_the_timeline_records_who_moved_it_and_why() -> None:
    app = _application(ApplicationStatus.PARTNER_ACKNOWLEDGED)
    await applications.transition(
        FakeSession(),
        app,
        ApplicationStatus.DOCS_REQUESTED,
        actor="partner:BOM-NAGPUR-01",
        reason="Caste certificate is illegible.",
    )
    entry = app.status_history[-1]
    assert entry["status"] == "DOCS_REQUESTED"
    assert entry["actor"] == "partner:BOM-NAGPUR-01"
    assert entry["reason"] == "Caste certificate is illegible."
    assert entry["at"], "every entry is timestamped"


async def test_history_is_reassigned_not_mutated_in_place() -> None:
    """SQLAlchemy does not track in-place JSONB mutation; a lost update is silent."""
    app = _application(ApplicationStatus.SUBMITTED)
    before = app.status_history
    await applications.transition(
        FakeSession(), app, ApplicationStatus.PARTNER_ACKNOWLEDGED, actor="partner"
    )
    assert app.status_history is not before


async def test_the_illegal_transition_message_says_what_is_allowed() -> None:
    """An error a partner-side developer can act on without reading our source."""
    app = _application(ApplicationStatus.SUBMITTED)
    with pytest.raises(applications.IllegalTransition) as caught:
        await applications.transition(
            FakeSession(), app, ApplicationStatus.DISBURSED, actor="partner"
        )
    assert "PARTNER_ACKNOWLEDGED" in str(caught.value)


# --- consent -------------------------------------------------------------------------------


async def test_nothing_is_stored_without_an_explicit_grant() -> None:
    """DPDP Act 2023: consent is a precondition, not a checkbox we default to true."""
    from app.services import citizens

    session = FakeSession()
    with pytest.raises(citizens.ConsentRequired):
        await citizens.record_consent(session, granted=False, purpose="anything")
    assert session.added == [], "a refused grant writes no row at all"


async def test_a_granted_consent_records_its_policy_version() -> None:
    from app.core.config import settings
    from app.services import citizens

    session = FakeSession()
    consent = await citizens.record_consent(session, granted=True, purpose="eligibility")
    assert consent.policy_version == settings.CONSENT_POLICY_VERSION
    assert consent.granted_at is not None


def test_the_consent_ip_is_hashed_not_stored() -> None:
    from app.services import citizens

    hashed = citizens.hash_ip("203.0.113.7")
    assert hashed is not None
    assert "203.0.113.7" not in hashed
    assert len(hashed) == 64
    assert citizens.hash_ip(None) is None
