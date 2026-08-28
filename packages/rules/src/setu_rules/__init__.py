"""SETU deterministic scheme eligibility engine.

Eligibility is decided here and nowhere else. A language model may extract facts into a
profile before this runs, and may restate the reasons this returns afterwards, but it
never participates in the verdict.
"""

from setu_rules.engine import evaluate, evaluate_scheme, indicative_amount, run
from setu_rules.loader import RuleLoadError, load_schemes, rules_digest
from setu_rules.models import (
    Family,
    MatchResult,
    MatchRun,
    NextQuestion,
    Provenance,
    Reason,
    Rule,
    Scheme,
    Severity,
    Verdict,
)
from setu_rules.profile import FIELDS, PROJECT_SECTORS, SOCIAL_CATEGORIES, validate_profile
from setu_rules.questions import field_impact, next_best_question
from setu_rules.safe_eval import UNKNOWN, RuleSyntaxError, compile_expression, evaluate_node
from setu_rules.version import ENGINE_VERSION

__all__ = [
    "ENGINE_VERSION",
    "FIELDS",
    "PROJECT_SECTORS",
    "SOCIAL_CATEGORIES",
    "UNKNOWN",
    "Family",
    "MatchResult",
    "MatchRun",
    "NextQuestion",
    "Provenance",
    "Reason",
    "Rule",
    "RuleLoadError",
    "RuleSyntaxError",
    "Scheme",
    "Severity",
    "Verdict",
    "compile_expression",
    "evaluate",
    "evaluate_node",
    "evaluate_scheme",
    "field_impact",
    "indicative_amount",
    "load_schemes",
    "next_best_question",
    "rules_digest",
    "run",
    "validate_profile",
]
