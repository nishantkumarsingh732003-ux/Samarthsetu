"""Golden-file snapshot.

Every rule change shows up as a readable diff in `golden/expected.json` during review,
so a reviewer sees exactly which citizens' verdicts moved — not just that a YAML line
changed.

Regenerate deliberately, never reflexively:

    python packages/rules/scripts/regenerate_golden.py
"""

import json
from pathlib import Path

from setu_rules import run

GOLDEN = Path(__file__).parent / "golden" / "expected.json"

# Each case is (name, profile). Keep them ordered; the file is diffed as text.
CASES: list[tuple[str, dict]] = [
    ("empty_profile", {}),
    ("category_only", {"category": "SC"}),
    (
        "sunita_street_vendor_80k",
        {
            "category": "SC",
            "project_sector": "TRADE",
            "occupation_type": "Vegetable vendor",
            "annual_family_income": 180000,
            "project_cost": 80000,
        },
    ),
    (
        "ramesh_workshop_12l",
        {
            "category": "SC",
            "project_sector": "MANUFACTURING",
            "occupation_type": "Furniture workshop",
            "annual_family_income": 420000,
            "project_cost": 1200000,
        },
    ),
    (
        "anjali_student_6l",
        {
            "category": "SC",
            "project_sector": "EDUCATION",
            "education_level": "Higher secondary",
            "admission_confirmed": True,
            "annual_family_income": 260000,
            "project_cost": 600000,
        },
    ),
    (
        "income_exactly_at_ceiling",
        {
            "category": "SC",
            "project_sector": "SERVICES",
            "annual_family_income": 500000,
            "project_cost": 100000,
        },
    ),
    (
        "income_one_rupee_over",
        {
            "category": "SC",
            "project_sector": "SERVICES",
            "annual_family_income": 500001,
            "project_cost": 100000,
        },
    ),
    (
        "micro_finance_boundary_140000",
        {
            "category": "SC",
            "project_sector": "ARTISAN",
            "annual_family_income": 200000,
            "project_cost": 140000,
        },
    ),
    (
        "micro_finance_boundary_140001_redirects",
        {
            "category": "SC",
            "project_sector": "ARTISAN",
            "annual_family_income": 200000,
            "project_cost": 140001,
        },
    ),
    (
        "student_without_confirmed_admission",
        {
            "category": "SC",
            "project_sector": "EDUCATION",
            "admission_confirmed": False,
            "annual_family_income": 260000,
            "project_cost": 600000,
        },
    ),
    (
        "non_sc_applicant",
        {
            "category": "OBC",
            "project_sector": "TRADE",
            "annual_family_income": 180000,
            "project_cost": 80000,
        },
    ),
    (
        "over_term_loan_ceiling",
        {
            "category": "SC",
            "project_sector": "MANUFACTURING",
            "annual_family_income": 300000,
            "project_cost": 6000000,
        },
    ),
]


def build_snapshot() -> dict:
    return {
        name: run(profile).to_dict()
        for name, profile in CASES
    }


def test_engine_output_matches_the_golden_file() -> None:
    assert GOLDEN.exists(), (
        "Golden file missing. Generate it with "
        "`python packages/rules/scripts/regenerate_golden.py`."
    )
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = build_snapshot()

    assert set(actual) == set(expected), "golden file case list is out of date"
    for name in expected:
        assert actual[name] == expected[name], (
            f"verdicts changed for {name!r}. If this is intended, review the diff and "
            "regenerate with scripts/regenerate_golden.py"
        )


def test_every_golden_case_is_reproducible_within_a_run() -> None:
    assert build_snapshot() == build_snapshot()
