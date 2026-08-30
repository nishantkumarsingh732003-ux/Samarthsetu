"""The console's own logic: action vocabulary, SLA states, and breakdown arithmetic.

The database-backed queries are proved against a live PostgreSQL rather than mocked —
an aggregate is only meaningful against the real schema. What is worth testing in
isolation is the layer between the API and the state machine, because that is where a
console can quietly grow the power to do something the lifecycle forbids.
"""

from __future__ import annotations

import pytest

from app.api.v1.routes.partner_console import ACTIONS, REASON_REQUIRED, _sla
from app.models.enums import ApplicationStatus, UserRole
from app.services import analytics
from app.services.applications import ALLOWED_TRANSITIONS


def test_every_console_action_maps_to_a_real_lifecycle_status() -> None:
    for action, target in ACTIONS.items():
        assert isinstance(target, ApplicationStatus), action


def test_the_console_cannot_invent_a_transition_the_engine_forbids() -> None:
    """Each action must be reachable from at least one state.

    An action that no state permits is a button that always 409s — dead UI at best,
    and at worst a sign the lifecycle changed and the console did not.
    """
    reachable = {target for targets in ALLOWED_TRANSITIONS.values() for target in targets}
    for action, target in ACTIONS.items():
        assert target in reachable, f"{action} can never legally be applied"


def test_the_console_offers_no_way_to_move_an_application_back_to_draft() -> None:
    assert ApplicationStatus.DRAFT not in ACTIONS.values()


def test_the_console_cannot_withdraw_on_a_citizens_behalf() -> None:
    """Withdrawal is the citizen's decision. A branch must reject and say why instead."""
    assert ApplicationStatus.WITHDRAWN not in ACTIONS.values()


def test_refusing_and_asking_for_more_both_require_a_reason() -> None:
    assert {"REJECT", "REQUEST_DOCS"} == REASON_REQUIRED
    assert set(ACTIONS) >= REASON_REQUIRED


# --- the SLA clock -------------------------------------------------------------------


@pytest.mark.parametrize(
    ("days_open", "turnaround", "expected"),
    [
        (0, 30, "ON_TRACK"),
        (10, 30, "ON_TRACK"),
        (29, 30, "DUE"),
        (30, 30, "DUE"),
        (31, 30, "BREACHED"),
        (99, 30, "BREACHED"),
    ],
)
def test_the_sla_clock_reports_the_right_state(
    days_open: int, turnaround: int, expected: str
) -> None:
    assert _sla(days_open, turnaround)[1] == expected


def test_a_partner_with_no_stated_turnaround_is_unknown_not_breached() -> None:
    """Absence of a commitment is not a failure to meet one."""
    days, state = _sla(500, None)
    assert state == "UNKNOWN"
    assert days is None


# --- breakdown arithmetic --------------------------------------------------------------


def test_shares_sum_to_one() -> None:
    rows = analytics._breakdown([("a", 3), ("b", 1)], {})
    assert sum(row["share"] for row in rows) == pytest.approx(1.0)
    assert rows[0]["share"] == pytest.approx(0.75)


def test_an_empty_breakdown_does_not_divide_by_zero() -> None:
    assert analytics._breakdown([], {}) == []


def test_a_single_zero_row_does_not_divide_by_zero() -> None:
    rows = analytics._breakdown([("a", 0)], {})
    assert rows[0]["share"] == 0.0


def test_language_keys_render_in_their_own_script() -> None:
    """A ministry analyst reading a language chart should see the language, not a code."""
    rows = analytics._breakdown([("ta", 2), ("hi", 1)], analytics.LANGUAGE_LABELS)
    assert {row["label"] for row in rows} == {"தமிழ்", "हिन्दी"}


def test_an_unlabelled_key_falls_back_to_something_readable() -> None:
    rows = analytics._breakdown([("NBFC_MFI", 1)], {})
    assert rows[0]["label"] == "Nbfc Mfi"


# --- roles ---------------------------------------------------------------------------


def test_there_are_exactly_three_roles() -> None:
    assert {r.value for r in UserRole} == {"CITIZEN", "PARTNER", "ADMIN"}
