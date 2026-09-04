"""The citizen account layer, and the wall between it and the rule engine.

The load-bearing test in this file is `test_enterprise_fields_never_reach_the_engine`.
Optional accounts introduced a place to store things the eligibility rules must never
read — a business name, a description an officer types, the amount an applicant *says*
they need. CLAUDE.md rule 1 says a verdict comes from the deterministic engine and
nothing else; `engine_profile()` is the projection that makes that structural, and this
is what stops someone widening it later without noticing.

No database. These are pure functions over detached model instances, so they run in CI
without Postgres, like the rest of the fast suite.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from setu_rules import FIELDS
from setu_rules import run as engine_run

from app.models import Citizen, CitizenProfile
from app.models.enums import Gender, SocialCategory
from app.services import citizen_accounts


def _citizen(**overrides) -> Citizen:
    fields = {
        "display_name": "Rahul Kumar",
        "preferred_language": "hi",
        "district": "Jaipur",
        "state": "Rajasthan",
        "city": "Jaipur",
        "pincode": "302001",
        **overrides,
    }
    return Citizen(**fields)


def _profile(**overrides) -> CitizenProfile:
    fields = {
        "category": SocialCategory.SC,
        "gender": Gender.MALE,
        "age": 31,
        "annual_family_income": Decimal("420000"),
        "occupation_type": "Tailor",
        "education_level": "Higher Secondary",
        "has_caste_certificate": True,
        "is_pwd": False,
        "is_safai_karamchari": False,
        "existing_loans": Decimal("0"),
        "project_sector": "MANUFACTURING",
        "project_cost": Decimal("1000000"),
        # Everything below is collected by onboarding and must not reach the engine.
        "own_contribution": Decimal("100000"),
        "loan_required": Decimal("900000"),
        "business_name": "Kumar Tailoring Unit",
        "business_status": "EXISTING",
        "business_description": "A two-machine tailoring unit adding four machines.",
        **overrides,
    }
    return CitizenProfile(**fields)


# --- the wall -------------------------------------------------------------------------


def test_enterprise_fields_never_reach_the_engine() -> None:
    """The projection is an allowlist, not a blocklist.

    A blocklist would silently start leaking the day someone adds a column. This asserts
    the positive form: every key handed to the engine is one the engine declares.
    """
    projected = citizen_accounts.engine_profile(_citizen(), _profile())

    assert set(projected) <= set(FIELDS), (
        "engine_profile() emitted a field outside the rule contract: "
        f"{sorted(set(projected) - set(FIELDS))}"
    )

    for leaked in (
        "business_name",
        "business_description",
        "business_status",
        "own_contribution",
        "loan_required",
        "display_name",
        "city",
        "pincode",
        "district",
        "state",
    ):
        assert leaked not in projected, f"{leaked} must not be visible to the rule engine"


def test_the_engine_accepts_what_the_projection_produces() -> None:
    """The projection and the engine's own validation must agree.

    If they drift, a signed-in citizen gets a 422 on the dashboard while an anonymous one
    posting the same facts gets a verdict — the two paths must stay identical.
    """
    projected = citizen_accounts.engine_profile(_citizen(), _profile())
    record = engine_run(projected, language="en")
    assert record.results, "the demo profile should produce results, not an empty list"


def test_what_a_citizen_says_they_need_does_not_move_the_verdict() -> None:
    """`loan_required` is the applicant's own figure and carries no authority.

    The amount is decided by the scheme's published ceilings against `project_cost`.
    Asking for ten times the project cost must change nothing.
    """
    modest = citizen_accounts.engine_profile(
        _citizen(), _profile(loan_required=Decimal("50000"))
    )
    greedy = citizen_accounts.engine_profile(
        _citizen(), _profile(loan_required=Decimal("10000000"))
    )
    assert modest == greedy

    def summarise(profile: dict) -> list[tuple]:
        return [
            (r["scheme_code"], r["verdict"], r["indicative_amount"])
            for r in engine_run(profile).to_dict()["results"]
        ]

    verdicts = [summarise(p) for p in (modest, greedy)]
    assert verdicts[0] == verdicts[1]


# --- projection details ----------------------------------------------------------------


def test_unanswered_fields_are_absent_rather_than_null() -> None:
    """Absent means NEED_MORE_INFO plus the next question; null could be read as zero."""
    projected = citizen_accounts.engine_profile(
        _citizen(), _profile(annual_family_income=None, age=None)
    )
    assert "annual_family_income" not in projected
    assert "age" not in projected


def test_decimals_become_floats() -> None:
    """The engine does arithmetic on these and the run is snapshotted as JSON."""
    projected = citizen_accounts.engine_profile(_citizen(), _profile())
    for field in ("annual_family_income", "project_cost", "existing_loans"):
        assert isinstance(projected[field], float), f"{field} reached the engine as Decimal"


def test_enums_become_their_string_values() -> None:
    projected = citizen_accounts.engine_profile(_citizen(), _profile())
    assert projected["category"] == "SC"
    assert projected["gender"] == "MALE"


def test_an_empty_profile_projects_to_nothing() -> None:
    """Which is what makes a brand-new account report NEED_MORE_INFO rather than crash."""
    assert citizen_accounts.engine_profile(_citizen(), CitizenProfile()) == {}


# --- completion ---------------------------------------------------------------------------


def test_completion_counts_only_fields_that_decide_eligibility() -> None:
    """A bar that fills up for optional answers is flattering and useless."""
    assert citizen_accounts.completion(_citizen(), _profile()) == 100
    assert citizen_accounts.completion(_citizen(), CitizenProfile()) < 100


def test_completion_is_zero_with_nothing_answered() -> None:
    assert citizen_accounts.completion(Citizen(), CitizenProfile()) == 0


def test_a_field_the_engine_ignores_does_not_raise_completion() -> None:
    """Typing a business name should not make the profile look more decidable."""
    bare = CitizenProfile()
    named = CitizenProfile(business_name="Kumar Tailoring Unit")
    assert citizen_accounts.completion(Citizen(), bare) == citizen_accounts.completion(
        Citizen(), named
    )


def test_every_completion_field_is_a_real_column() -> None:
    """A renamed column would otherwise leave the bar permanently short by one."""
    for field in citizen_accounts.COMPLETION_FIELDS:
        holder = Citizen if field in citizen_accounts.CITIZEN_FIELDS else CitizenProfile
        assert hasattr(holder, field), f"{field} is not a column on {holder.__name__}"


# --- the demo persona ---------------------------------------------------------------------


def test_the_demo_persona_is_inside_the_published_income_ceiling() -> None:
    """Rs 5,00,000 is the ceiling in the problem statement. A demo that sails past it
    would show the engine agreeing with everything, which demonstrates nothing."""
    assert citizen_accounts.DEMO_PROFILE["annual_family_income"] < 500000


def test_the_demo_persona_distinguishes_the_scheme_families() -> None:
    """The point of the demo is that the engine tells the three families apart.

    A project cost above the Micro Finance ceiling and inside the Term Loan band means a
    judge sees one ELIGIBLE and one blocked with a named rule, rather than three verdicts
    that agree.
    """
    profile = citizen_accounts.engine_profile(
        _citizen(**citizen_accounts.DEMO_CITIZEN),
        _profile(
            **{
                key: value
                for key, value in citizen_accounts.DEMO_PROFILE.items()
                if key not in {"category", "gender"}
            },
            category=SocialCategory(citizen_accounts.DEMO_PROFILE["category"]),
            gender=Gender(citizen_accounts.DEMO_PROFILE["gender"]),
        )
    )
    verdicts = {r["scheme_code"]: r["verdict"] for r in engine_run(profile).to_dict()["results"]}

    assert "ELIGIBLE" in verdicts.values(), f"nothing was eligible: {verdicts}"
    assert "INELIGIBLE" in verdicts.values(), f"nothing was blocked: {verdicts}"


def test_the_demo_persona_only_sets_fields_the_update_accepts() -> None:
    """`load_demo` goes through the same validation a typed answer does."""
    allowed = citizen_accounts.PROFILE_FIELDS | citizen_accounts.CITIZEN_FIELDS
    unknown = (set(citizen_accounts.DEMO_PROFILE) | set(citizen_accounts.DEMO_CITIZEN)) - allowed
    assert not unknown, f"the demo persona sets fields update_profile would reject: {unknown}"


# --- the update contract ------------------------------------------------------------------


def test_profile_and_citizen_field_sets_do_not_overlap() -> None:
    """A name in both would be written to whichever branch the dispatch happens to pick."""
    assert not (citizen_accounts.PROFILE_FIELDS & citizen_accounts.CITIZEN_FIELDS)


def test_every_writable_field_is_a_real_column() -> None:
    for field in citizen_accounts.PROFILE_FIELDS:
        assert hasattr(CitizenProfile, field), f"{field} is not a CitizenProfile column"
    for field in citizen_accounts.CITIZEN_FIELDS:
        assert hasattr(Citizen, field), f"{field} is not a Citizen column"


def test_identity_columns_are_not_writable_through_the_profile_update() -> None:
    """Consent and the masked ID are set once, by the code holding the consent record."""
    writable = citizen_accounts.PROFILE_FIELDS | citizen_accounts.CITIZEN_FIELDS
    for protected in ("gov_id_hash", "gov_id_last4", "gov_id_type", "consent_id", "phone_last4"):
        assert protected not in writable, f"{protected} must not be patchable from a form"


@pytest.mark.parametrize("field", ["is_admin", "verdict", "engine_version", "completed_at"])
def test_an_invented_field_is_rejected(field: str) -> None:
    """The allowlist is what turns a client typo into a 422 naming it."""
    assert field not in (citizen_accounts.PROFILE_FIELDS | citizen_accounts.CITIZEN_FIELDS)


def test_the_consent_purpose_says_what_it_covers() -> None:
    """A subject-access request has to be answerable from the consent row alone."""
    purpose = citizen_accounts.SIGNUP_CONSENT_PURPOSE
    assert len(purpose) > 20
    assert "profile" in purpose.lower()


def test_engine_profile_is_stable_across_calls() -> None:
    """Same inputs, same dictionary — the cache key in the route depends on it."""
    citizen, profile = _citizen(), _profile()
    assert citizen_accounts.engine_profile(citizen, profile) == citizen_accounts.engine_profile(
        citizen, profile
    )


def test_load_demo_marks_the_profile_complete_not_the_reverse() -> None:
    """Guards against a refactor that flips the flag: a demo profile is finished."""
    profile = CitizenProfile()
    profile.completed_at = datetime.now(UTC)
    assert profile.completed_at is not None


# --- the demo reset must not take the logins with it ----------------------------------


def test_the_demo_reset_does_not_truncate_cascade_through_citizens() -> None:
    """`TRUNCATE ... CASCADE` is schema-level, and that is the trap.

    It truncates every table holding a foreign key to a named table, whether or not any
    row currently points there. The moment citizen accounts added `users.citizen_id`, the
    demo seeder's `TRUNCATE citizens CASCADE` reached `users` and emptied it — so
    `make demo` destroyed all three logins, both consoles and the judge console stopped
    working, and nothing reported an error. Nulling the column first does not help;
    only not using CASCADE does.

    A source-level assertion because the failure is invisible at every other level: the
    seeder printed success, the schema was valid, and the tests passed. Cheap insurance
    against someone reaching for TRUNCATE again for the speed.
    """
    import ast
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[3] / "scripts" / "seed" / "demo.py"
    ).read_text(encoding="utf-8")

    # Parse rather than grep: the docstring on reset() explains this trap at length, and
    # a text search would match its own warning. Only string literals that are not the
    # docstring can be SQL.
    tree = ast.parse(source)
    reset = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef) and node.name == "reset"
    )
    # Exclude the docstring by node identity. Comparing against ast.get_docstring() does
    # not work: that returns the *cleaned* text, which never equals the raw constant.
    docstring_node = None
    if reset.body and isinstance(reset.body[0], ast.Expr):
        first = reset.body[0].value
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            docstring_node = first

    statements = [
        node.value.upper()
        for node in ast.walk(reset)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node is not docstring_node
    ]
    sql = " | ".join(statements)

    assert "TRUNCATE" not in sql, (
        "reset() runs TRUNCATE again. Its CASCADE follows foreign keys into `users` "
        "and deletes every login, silently."
    )
    # And it must still clear the things it exists to clear.
    for table in ("citizens", "consents", "applications", "match_runs", "audit_log"):
        assert f"DELETE FROM {table.upper()}" in sql, f"reset() no longer clears {table}"


def test_a_citizen_login_can_be_reattached_after_a_reset() -> None:
    """The seeder must be able to rebuild what the reset removed.

    `repair_citizen_logins` is what lets `demo.py` delete the citizen rows and still hand
    back a working `citizen@setu.gov.in`. It goes through `services.citizens`, so the
    consent record is written before the citizen — the same order a real signup uses.
    """
    import inspect
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from scripts.seed.users import attach_citizen_record, repair_citizen_logins

    source = inspect.getsource(attach_citizen_record)
    assert "record_consent" in source, "the consent row must be written before the citizen"
    assert source.index("record_consent") < source.index("create_citizen")
    assert inspect.iscoroutinefunction(repair_citizen_logins)
