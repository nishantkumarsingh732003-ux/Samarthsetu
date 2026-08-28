"""Verdict logic, ranking determinism, and the three demo personas."""

import pytest

from setu_rules import ENGINE_VERSION, Verdict, evaluate, load_schemes, run

SUNITA = {
    "category": "SC",
    "project_sector": "TRADE",
    "occupation_type": "Vegetable vendor",
    "annual_family_income": 180000,
    "project_cost": 80000,
}
RAMESH = {
    "category": "SC",
    "project_sector": "MANUFACTURING",
    "occupation_type": "Furniture workshop",
    "annual_family_income": 420000,
    "project_cost": 1200000,
}
ANJALI = {
    "category": "SC",
    "project_sector": "EDUCATION",
    "education_level": "Higher secondary",
    "admission_confirmed": True,
    "annual_family_income": 260000,
    "project_cost": 600000,
}


def top(profile) -> str:
    return evaluate(profile)[0].scheme_code


def result_for(profile, code):
    return next(r for r in evaluate(profile) if r.scheme_code == code)


# ------------------------------------------------------------------- the three personas


def test_street_vendor_is_routed_to_micro_finance() -> None:
    assert top(SUNITA) == "NSFDC_MICRO_FINANCE"
    assert result_for(SUNITA, "NSFDC_MICRO_FINANCE").verdict is Verdict.ELIGIBLE


def test_workshop_owner_is_routed_to_term_loan() -> None:
    assert top(RAMESH) == "NSFDC_TERM_LOAN"
    assert result_for(RAMESH, "NSFDC_TERM_LOAN").verdict is Verdict.ELIGIBLE


def test_workshop_owner_is_redirected_off_micro_finance() -> None:
    """Ramesh asks for Rs 12,00,000; micro finance must refuse AND point onward."""
    micro = result_for(RAMESH, "NSFDC_MICRO_FINANCE")
    assert micro.verdict is Verdict.INELIGIBLE
    assert micro.redirect_suggestion == "NSFDC_TERM_LOAN"
    assert "MF_PROJECT_COST_BAND" in {r.rule_id for r in micro.blocked_because}


def test_student_is_routed_to_education_loan() -> None:
    assert top(ANJALI) == "NSFDC_EDUCATION_LOAN"
    assert result_for(ANJALI, "NSFDC_EDUCATION_LOAN").verdict is Verdict.ELIGIBLE


def test_student_is_blocked_from_enterprise_schemes_with_a_redirect() -> None:
    micro = result_for(ANJALI, "NSFDC_MICRO_FINANCE")
    assert micro.verdict is Verdict.INELIGIBLE
    assert micro.redirect_suggestion == "NSFDC_EDUCATION_LOAN"


def test_each_persona_exercises_a_different_family() -> None:
    families = {top(p) for p in (SUNITA, RAMESH, ANJALI)}
    assert len(families) == 3


# --------------------------------------------------------------------------- verdicts


def test_over_income_is_ineligible_everywhere() -> None:
    profile = {**SUNITA, "annual_family_income": 750000}
    assert all(r.verdict is Verdict.INELIGIBLE for r in evaluate(profile))


def test_non_sc_applicant_is_ineligible_everywhere() -> None:
    profile = {**SUNITA, "category": "GENERAL"}
    assert all(r.verdict is Verdict.INELIGIBLE for r in evaluate(profile))


def test_empty_profile_needs_more_info_rather_than_refusing() -> None:
    """Nothing known must never be read as "does not qualify"."""
    results = evaluate({})
    assert all(r.verdict is Verdict.NEED_MORE_INFO for r in results)
    assert all(r.missing_fields for r in results)


def test_missing_fields_only_lists_fields_that_are_actually_absent() -> None:
    profile = {"category": "SC"}
    micro = result_for(profile, "NSFDC_MICRO_FINANCE")
    assert "category" not in micro.missing_fields
    assert "annual_family_income" in micro.missing_fields


def test_need_more_info_confidence_reflects_how_much_is_decided() -> None:
    nothing = result_for({}, "NSFDC_MICRO_FINANCE")
    partial = result_for({"category": "SC", "annual_family_income": 100000}, "NSFDC_MICRO_FINANCE")
    assert 0.0 <= nothing.confidence < partial.confidence < 1.0


def test_a_definite_block_beats_unknown_fields() -> None:
    """Ineligible on a known rule stays ineligible even with other facts missing."""
    result = result_for({"annual_family_income": 900000}, "NSFDC_MICRO_FINANCE")
    assert result.verdict is Verdict.INELIGIBLE
    assert result.confidence == 1.0


def test_matched_because_is_populated_for_satisfied_rules() -> None:
    micro = result_for(SUNITA, "NSFDC_MICRO_FINANCE")
    ids = {r.rule_id for r in micro.matched_because}
    assert {"MF_CATEGORY_SC", "MF_INCOME_CEILING", "MF_PROJECT_COST_BAND"} <= ids
    assert all(r.message for r in micro.matched_because)


def test_every_reason_carries_a_quotable_rule_id_and_message() -> None:
    for profile in (SUNITA, RAMESH, ANJALI, {}, {"category": "GENERAL"}):
        for result in evaluate(profile):
            for reason in (*result.matched_because, *result.blocked_because, *result.warnings):
                assert reason.rule_id and reason.message


# ---------------------------------------------------------------------------- ranking


def test_ranking_is_a_pure_function() -> None:
    first = [r.scheme_code for r in evaluate(SUNITA)]
    for _ in range(5):
        assert [r.scheme_code for r in evaluate(SUNITA)] == first


def test_ranks_are_dense_and_start_at_one() -> None:
    assert [r.rank for r in evaluate(SUNITA)] == [1, 2, 3]


def test_ineligible_schemes_are_returned_but_ranked_last() -> None:
    """Transparency beats hiding: the blocked card is still shown, with its reason."""
    results = evaluate(RAMESH)
    assert len(results) == 3
    assert results[-1].verdict is Verdict.INELIGIBLE
    assert results[-1].blocked_because


def test_tightest_fitting_scheme_ranks_first() -> None:
    """Both schemes can fund Rs 80,000; the one sized for it should win."""
    results = [r for r in evaluate(SUNITA) if r.verdict is not Verdict.INELIGIBLE]
    assert results[0].scheme_code == "NSFDC_MICRO_FINANCE"


def test_localisation_falls_back_to_english_for_untranslated_languages() -> None:
    hindi = result_for(SUNITA, "NSFDC_MICRO_FINANCE")
    marathi = next(
        r for r in evaluate(SUNITA, language="mr") if r.scheme_code == "NSFDC_MICRO_FINANCE"
    )
    assert all(r.message for r in marathi.matched_because)
    assert len(marathi.matched_because) == len(hindi.matched_because)


def test_hindi_messages_differ_from_english() -> None:
    en = next(r for r in evaluate(RAMESH) if r.scheme_code == "NSFDC_MICRO_FINANCE")
    hi = next(
        r for r in evaluate(RAMESH, language="hi") if r.scheme_code == "NSFDC_MICRO_FINANCE"
    )
    assert en.blocked_because[0].message != hi.blocked_because[0].message


# ------------------------------------------------------------------------- match run


def test_run_records_everything_needed_to_replay_the_decision() -> None:
    record = run(SUNITA)
    assert record.engine_version == ENGINE_VERSION
    assert record.rules_digest
    assert record.input_snapshot == dict(sorted(SUNITA.items()))
    assert len(record.results) == 3


def test_match_run_serialises_to_plain_json_types() -> None:
    import json

    payload = json.dumps(run(RAMESH).to_dict())
    assert "NSFDC_TERM_LOAN" in payload


def test_every_result_carries_provenance() -> None:
    """CLAUDE.md rule 2: no figure reaches the UI without its sourcing status."""
    for result in evaluate(SUNITA):
        assert result.provenance is not None
        assert result.needs_verification is True


def test_unknown_profile_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown profile field"):
        evaluate({"favourite_colour": "blue"})


def test_value_outside_controlled_vocabulary_is_rejected() -> None:
    with pytest.raises(ValueError, match="must be one of"):
        evaluate({"category": "SCHEDULED_CASTE"})


def test_all_three_scheme_families_are_present() -> None:
    families = {s.family for s in load_schemes()}
    assert len(families) == 3
