"""Adaptive questioning: ask only what can change the answer.

`next_best_question` scores every field the citizen has not supplied by how many
currently-undecided HARD_BLOCK rules it would resolve, across all schemes. The field
that unblocks the most rules wins. Ties break on the field's declared priority, then
alphabetically, so the result is a pure function of the profile.

The effect at the UI layer: a citizen is never asked their education level to decide a
micro-finance application, because that field cannot move any rule.
"""

from __future__ import annotations

from typing import Any

from setu_rules.loader import load_schemes
from setu_rules.models import NextQuestion, Scheme, Severity
from setu_rules.safe_eval import UNKNOWN, evaluate_node


def _undecided_hard_rules(
    profile: dict[str, Any], schemes: tuple[Scheme, ...]
) -> list[tuple[Scheme, Any]]:
    """Every HARD_BLOCK rule that is still undecided *and still matters*.

    A scheme with even one rule that is definitively blocking is settled — no further
    answer can revive it, so none of its other unknown rules are worth a question. This
    is what stops us asking a student to confirm their admission for a scheme their
    income already ruled out.
    """
    undecided: list[tuple[Scheme, Any]] = []

    for scheme in schemes:
        hard_rules = [r for r in scheme.rules if r.severity is Severity.HARD_BLOCK]
        outcomes = [(rule, evaluate_node(rule.when, profile)) for rule in hard_rules]

        if any(outcome is True for _, outcome in outcomes):
            continue  # already ineligible; nothing left to ask about this scheme

        undecided.extend((scheme, rule) for rule, outcome in outcomes if outcome is UNKNOWN)

    return undecided


def field_impact(
    profile: dict[str, Any], schemes: tuple[Scheme, ...] | None = None
) -> dict[str, dict[str, Any]]:
    """Map each askable field to the rules and schemes it would resolve."""
    catalogue = schemes if schemes is not None else load_schemes()
    impact: dict[str, dict[str, Any]] = {}

    for scheme, rule in _undecided_hard_rules(profile, catalogue):
        for name in rule.fields:
            if profile.get(name) is not None:
                continue  # already known; not a question we can ask
            entry = impact.setdefault(name, {"rules": set(), "schemes": set()})
            entry["rules"].add(rule.id)
            entry["schemes"].add(scheme.code)

    return impact


def next_best_question(
    profile: dict[str, Any], schemes: tuple[Scheme, ...] | None = None
) -> NextQuestion | None:
    """The single field that removes the most ambiguity, or None if nothing is left."""
    from setu_rules.profile import FIELDS  # local import avoids a cycle at module load

    impact = field_impact(profile, schemes)
    if not impact:
        return None

    def sort_key(item: tuple[str, dict[str, Any]]) -> tuple:
        name, entry = item
        field = FIELDS[name]
        # Most rules resolved first; then the authored priority; then the name.
        return (-len(entry["rules"]), field.priority, name)

    name, entry = min(impact.items(), key=sort_key)
    field = FIELDS[name]

    return NextQuestion(
        field_name=name,
        question_i18n=dict(field.question_i18n),
        kind=field.kind,
        choices=field.choices,
        resolves_rules=tuple(sorted(entry["rules"])),
        resolves_schemes=tuple(sorted(entry["schemes"])),
    )
