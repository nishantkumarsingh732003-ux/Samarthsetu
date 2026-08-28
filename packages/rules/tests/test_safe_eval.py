"""The evaluator must be safe and must never treat "unknown" as "no"."""

import pytest

from setu_rules.safe_eval import (
    UNKNOWN,
    RuleSyntaxError,
    compile_expression,
    evaluate_node,
    referenced_fields,
)


def ev(expr: str, **profile):
    return evaluate_node(compile_expression(expr), profile)


# --------------------------------------------------------------------------- safety


@pytest.mark.parametrize(
    "expr",
    [
        "__import__('os').system('rm -rf /')",
        "open('/etc/passwd').read()",
        "profile.annual_family_income.__class__",
        "[x for x in profile]",
        "lambda: 1",
        "profile['annual_family_income']",
        "exec('x=1')",
        "profile.annual_family_income + 1 > 2",
        "unknown_name > 1",
        "profile.no_such_field > 1",
    ],
)
def test_dangerous_or_unknown_expressions_are_rejected(expr: str) -> None:
    with pytest.raises(RuleSyntaxError):
        compile_expression(expr)


def test_chained_comparisons_are_rejected() -> None:
    with pytest.raises(RuleSyntaxError, match="chained"):
        compile_expression("100 < profile.age < 200")


# ------------------------------------------------------------------ three-valued logic


def test_comparison_against_a_missing_field_is_unknown_not_false() -> None:
    assert ev("profile.annual_family_income > 500000", annual_family_income=None) is UNKNOWN


def test_known_field_compares_normally() -> None:
    assert ev("profile.annual_family_income > 500000", annual_family_income=600000) is True
    assert ev("profile.annual_family_income > 500000", annual_family_income=400000) is False


def test_false_dominates_and() -> None:
    """A definite False decides an AND even when the other side is unknown."""
    expr = "profile.annual_family_income > 500000 and profile.project_cost > 140000"
    assert ev(expr, annual_family_income=100000, project_cost=None) is False


def test_unknown_propagates_through_and_when_not_decided() -> None:
    expr = "profile.annual_family_income > 500000 and profile.project_cost > 140000"
    assert ev(expr, annual_family_income=600000, project_cost=None) is UNKNOWN


def test_true_dominates_or() -> None:
    expr = "profile.annual_family_income > 500000 or profile.project_cost > 140000"
    assert ev(expr, annual_family_income=600000, project_cost=None) is True


def test_unknown_propagates_through_or_when_not_decided() -> None:
    expr = "profile.annual_family_income > 500000 or profile.project_cost > 140000"
    assert ev(expr, annual_family_income=100000, project_cost=None) is UNKNOWN


def test_not_of_unknown_is_unknown() -> None:
    assert ev("not profile.is_pwd == true", is_pwd=None) is UNKNOWN


def test_yaml_style_literals_are_supported() -> None:
    assert ev("profile.admission_confirmed == false", admission_confirmed=False) is True
    assert ev("profile.admission_confirmed == true", admission_confirmed=True) is True
    assert ev("profile.admission_confirmed == false", admission_confirmed=None) is UNKNOWN


def test_membership_operator() -> None:
    assert ev("profile.category in ['SC', 'ST']", category="SC") is True
    assert ev("profile.category in ['SC', 'ST']", category="OBC") is False
    assert ev("profile.category in ['SC', 'ST']", category=None) is UNKNOWN


def test_unknown_has_no_truthiness() -> None:
    """Guards against `if value:` silently treating UNKNOWN as False."""
    with pytest.raises(TypeError):
        bool(UNKNOWN)


def test_referenced_fields_finds_every_field() -> None:
    node = compile_expression(
        "profile.annual_family_income > 500000 and profile.category != 'SC'"
    )
    assert referenced_fields(node) == {"annual_family_income", "category"}
