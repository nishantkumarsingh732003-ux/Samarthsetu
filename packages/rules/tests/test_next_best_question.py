"""The adaptive questionnaire must only ask what can change the outcome."""

from setu_rules import Verdict, evaluate, field_impact, next_best_question


def test_first_question_on_an_empty_profile_is_the_highest_impact_field() -> None:
    """Category gates all three schemes, so it resolves the most rules."""
    question = next_best_question({})
    assert question is not None
    assert question.field_name == "category"
    assert len(question.resolves_schemes) == 3


def test_question_carries_everything_the_ui_needs() -> None:
    question = next_best_question({})
    assert question.question_i18n["en"]
    assert question.question_i18n["hi"]
    assert question.kind == "string"
    assert "SC" in question.choices


def test_answered_fields_are_never_asked_again() -> None:
    profile: dict = {}
    asked: list[str] = []
    while (question := next_best_question(profile)) is not None:
        assert question.field_name not in asked
        asked.append(question.field_name)
        profile[question.field_name] = _plausible_answer(question.field_name)
    assert asked


def test_a_complete_profile_has_no_next_question() -> None:
    profile = {
        "category": "SC",
        "project_sector": "TRADE",
        "annual_family_income": 180000,
        "project_cost": 80000,
    }
    assert next_best_question(profile) is None


def test_conversation_reaches_a_decision_within_six_questions() -> None:
    """Phase 3 promises "at most 6 questions"; the engine must make that achievable."""
    profile: dict = {}
    for _ in range(6):
        question = next_best_question(profile)
        if question is None:
            break
        profile[question.field_name] = _plausible_answer(question.field_name)

    assert next_best_question(profile) is None
    assert all(r.verdict is not Verdict.NEED_MORE_INFO for r in evaluate(profile))


def test_irrelevant_fields_are_never_proposed() -> None:
    """No rule references education_level, so it must never be asked."""
    profile: dict = {}
    proposed = set()
    while (question := next_best_question(profile)) is not None:
        proposed.add(question.field_name)
        profile[question.field_name] = _plausible_answer(question.field_name)
    assert "education_level" not in proposed
    assert "is_pwd" not in proposed
    assert "gender" not in proposed


def test_admission_is_only_asked_once_education_is_the_stated_purpose() -> None:
    enterprise = {"category": "SC", "project_sector": "TRADE", "annual_family_income": 180000}
    assert "admission_confirmed" not in field_impact(enterprise)

    education = {"category": "SC", "project_sector": "EDUCATION", "annual_family_income": 180000}
    assert "admission_confirmed" in field_impact(education)


def test_field_impact_reports_which_rules_a_field_would_resolve() -> None:
    impact = field_impact({})
    assert "MF_INCOME_CEILING" in impact["annual_family_income"]["rules"]
    assert "NSFDC_MICRO_FINANCE" in impact["annual_family_income"]["schemes"]


def test_next_best_question_is_deterministic() -> None:
    assert {next_best_question({}).field_name for _ in range(10)} == {"category"}


def test_a_decided_block_stops_further_questioning() -> None:
    """Once income rules everything out, there is nothing useful left to ask."""
    profile = {"category": "SC", "annual_family_income": 900000, "project_sector": "TRADE"}
    assert next_best_question(profile) is None
    assert all(r.verdict is Verdict.INELIGIBLE for r in evaluate(profile))


def _plausible_answer(field_name: str):
    return {
        "category": "SC",
        "project_sector": "TRADE",
        "annual_family_income": 180000,
        "project_cost": 80000,
        "admission_confirmed": True,
    }[field_name]
