"""Provenance and version discipline.

The digest test is the answer to "what happens when the rules change next April?":
edit the YAML, and CI fails until you bump ENGINE_VERSION and record the new digest.
Eligibility policy cannot change quietly.
"""

import pytest

from setu_rules import ENGINE_VERSION, load_schemes, rules_digest
from setu_rules.version import PINNED_RULES_DIGEST

SUPPORTED_LANGUAGES = ("en", "hi", "mr", "bn", "ta", "te")


def test_rule_changes_require_a_version_bump() -> None:
    assert rules_digest() == PINNED_RULES_DIGEST, (
        "The scheme YAML changed. Bump ENGINE_VERSION in src/setu_rules/version.py and "
        f"set PINNED_RULES_DIGEST to {rules_digest()!r}."
    )


def test_engine_version_is_semver() -> None:
    parts = ENGINE_VERSION.split(".")
    assert len(parts) == 3 and all(p.isdigit() for p in parts)


def test_every_scheme_declares_its_verification_status() -> None:
    """A figure with no source_url must be visibly unverified, never silently trusted."""
    for scheme in load_schemes():
        prov = scheme.provenance
        assert prov.last_verified_on, f"{scheme.code} has no last_verified_on"
        if not prov.source_url:
            assert prov.needs_verification, f"{scheme.code} has no source but claims verified"
            assert prov.verification_note, f"{scheme.code} needs a note saying what to verify"


def test_no_scheme_invents_a_circular_reference() -> None:
    """Until a real circular is located, circular_ref stays null."""
    for scheme in load_schemes():
        if scheme.provenance.circular_ref:
            assert scheme.provenance.source_url, (
                f"{scheme.code} cites a circular but gives no source_url"
            )


def test_education_loan_states_no_project_cost_band() -> None:
    """NSFDC caps the loan but states no band on course cost, so none is invented."""
    edu = next(s for s in load_schemes() if s.code == "NSFDC_EDUCATION_LOAN")
    assert edu.limits.min_project_cost is None
    assert edu.limits.max_project_cost is None
    assert edu.limits.max_loan_amount == 4000000
    assert edu.provenance.needs_verification


def test_project_cost_bands_match_the_problem_statement() -> None:
    """The figures the problem statement states are project-cost bands, not loan caps."""
    limits = {s.code: s.limits for s in load_schemes()}
    assert limits["NSFDC_MICRO_FINANCE"].max_project_cost == 140000
    assert limits["NSFDC_TERM_LOAN"].max_project_cost == 5000000
    assert all(scheme.max_funding_pct == 90 for scheme in limits.values())


def test_loan_caps_are_lower_than_the_project_bands() -> None:
    """The distinction that keeps us from overstating what a citizen can borrow."""
    limits = {s.code: s.limits for s in load_schemes()}
    assert limits["NSFDC_MICRO_FINANCE"].max_loan_amount == 125000
    assert limits["NSFDC_TERM_LOAN"].max_loan_amount == 4500000
    for code in ("NSFDC_MICRO_FINANCE", "NSFDC_TERM_LOAN"):
        assert limits[code].max_loan_amount < limits[code].max_project_cost


def test_interest_rates_sit_inside_the_problem_statement_band() -> None:
    """The problem statement says "typically 6.5% - 8%"; NSFDC states an exact rate
    per scheme. Refining within the band is allowed; leaving it is not."""
    for scheme in load_schemes():
        assert 6.5 <= scheme.limits.interest_rate_min <= 8.0
        assert 6.5 <= scheme.limits.interest_rate_max <= 8.0
        assert scheme.limits.interest_rate_min <= scheme.limits.interest_rate_max


def test_figures_with_no_single_value_stay_null() -> None:
    """The Educational Loan Scheme's tenure depends on disbursement status and its
    moratorium on course length. Neither reduces to one number, so neither is faked."""
    edu = next(s for s in load_schemes() if s.code == "NSFDC_EDUCATION_LOAN")
    assert edu.limits.tenure_months is None
    assert edu.limits.moratorium_months is None
    assert {q.field for q in edu.provenance.open_questions} >= {
        "tenure_months",
        "moratorium_months",
    }


def test_every_unresolved_figure_has_a_recorded_open_question() -> None:
    """An unknown must be written down as a question, not left as a silent null."""
    for scheme in load_schemes():
        assert scheme.provenance.open_questions, f"{scheme.code} declares no open questions"
        for question in scheme.provenance.open_questions:
            assert question.question.strip()


def test_every_scheme_cites_a_real_source_url() -> None:
    for scheme in load_schemes():
        assert scheme.provenance.source_url
        assert scheme.provenance.source_url.startswith("https://")


def test_rule_ids_are_unique_across_the_whole_catalogue() -> None:
    ids = [r.id for s in load_schemes() for r in s.rules]
    assert len(ids) == len(set(ids))


def test_every_rule_has_an_english_message() -> None:
    for scheme in load_schemes():
        for rule in scheme.rules:
            assert rule.message_i18n.get("en")


@pytest.mark.parametrize("language", ["mr", "bn", "ta", "te"])
def test_untranslated_languages_are_declared_not_silently_missing(language: str) -> None:
    """We would rather admit a translation gap than ship a machine-translated one."""
    for scheme in load_schemes():
        assert language in scheme.pending_translations


def test_translation_coverage_report() -> None:
    """Documents the current gap so it shows up in test output rather than in production."""
    covered = {lang: 0 for lang in SUPPORTED_LANGUAGES}
    total = 0
    for scheme in load_schemes():
        for rule in scheme.rules:
            total += 1
            for lang in SUPPORTED_LANGUAGES:
                if rule.message_i18n.get(lang):
                    covered[lang] += 1

    assert covered["en"] == total, "English is the fallback and must be complete"
    assert covered["hi"] == total, "Hindi is a priority language and must be complete"
