"""Safe expression evaluator for the rule DSL.

Two jobs:

1. `compile_expression` parses a `when:` string with Python's `ast` module, walks it
   against a strict node whitelist, and emits a small portable JSON tree. Nothing is
   ever `eval`-ed, no function calls or subscripts are reachable, and every field name
   is checked against the profile contract at compile time.

2. `evaluate_node` interprets that tree using **three-valued (Kleene) logic**. A
   comparison against a field the citizen has not told us yet is UNKNOWN, not False.
   That distinction is the whole basis of the NEED_MORE_INFO verdict: we never guess a
   citizen into ineligibility because a form was half-finished.

The JSON tree is the artefact the TypeScript engine consumes, so both runtimes
interpret exactly the same structure rather than each parsing the DSL themselves.
"""

from __future__ import annotations

import ast
from typing import Any, Final

from setu_rules.profile import FIELD_NAMES


class Unknown:
    """Third truth value. Singleton; falsy checks must use `is UNKNOWN`."""

    _instance: Unknown | None = None

    def __new__(cls) -> Unknown:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "UNKNOWN"

    def __bool__(self) -> bool:
        raise TypeError("UNKNOWN has no boolean value; compare with `is UNKNOWN`")


UNKNOWN: Final = Unknown()

Ternary = bool | Unknown
Node = dict[str, Any]

COMPARATORS: Final[dict[type[ast.cmpop], str]] = {
    ast.Eq: "==",
    ast.NotEq: "!=",
    ast.Lt: "<",
    ast.LtE: "<=",
    ast.Gt: ">",
    ast.GtE: ">=",
    ast.In: "in",
    ast.NotIn: "not in",
}


# YAML spells booleans and null in lower case; the DSL follows YAML, not Python.
YAML_LITERALS: Final[dict[str, Any]] = {
    "true": True,
    "false": False,
    "null": None,
    "True": True,
    "False": False,
    "None": None,
}


class RuleSyntaxError(ValueError):
    """Raised when a `when:` expression uses anything outside the whitelist."""


# --------------------------------------------------------------------------- compile


def compile_expression(source: str) -> Node:
    """Parse a `when:` string into a portable JSON node tree."""
    try:
        tree = ast.parse(source, mode="eval")
    except SyntaxError as exc:  # pragma: no cover - message passthrough
        raise RuleSyntaxError(f"cannot parse expression {source!r}: {exc}") from exc
    return _compile(tree.body, source)


def _compile(node: ast.AST, source: str) -> Node:
    if isinstance(node, ast.BoolOp):
        op = "and" if isinstance(node.op, ast.And) else "or"
        return {"op": op, "args": [_compile(v, source) for v in node.values]}

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return {"op": "not", "arg": _compile(node.operand, source)}

    if isinstance(node, ast.Compare):
        if len(node.ops) != 1 or len(node.comparators) != 1:
            raise RuleSyntaxError(
                f"chained comparisons are not supported in {source!r}; use `and`"
            )
        op_type = type(node.ops[0])
        if op_type not in COMPARATORS:
            raise RuleSyntaxError(f"comparison {op_type.__name__} not allowed in {source!r}")
        return {
            "op": "cmp",
            "operator": COMPARATORS[op_type],
            "left": _compile(node.left, source),
            "right": _compile(node.comparators[0], source),
        }

    if isinstance(node, ast.Attribute):
        if not isinstance(node.value, ast.Name) or node.value.id != "profile":
            raise RuleSyntaxError(
                f"only `profile.<field>` attribute access is allowed in {source!r}"
            )
        if node.attr not in FIELD_NAMES:
            raise RuleSyntaxError(
                f"unknown profile field {node.attr!r} in {source!r}; "
                "add it to setu_rules.profile.FIELDS first"
            )
        return {"op": "field", "name": node.attr}

    if isinstance(node, ast.Name):
        # The DSL is YAML-facing and language-neutral, so it spells literals the way
        # YAML does. Python's parser reads these as bare names, so map them here.
        if node.id in YAML_LITERALS:
            return {"op": "const", "value": YAML_LITERALS[node.id]}
        raise RuleSyntaxError(
            f"bare name {node.id!r} is not allowed in {source!r}; "
            "use profile.<field>, a quoted string, a number, true/false/null"
        )

    if isinstance(node, ast.Constant):
        if not isinstance(node.value, str | int | float | bool | type(None)):
            raise RuleSyntaxError(f"unsupported literal {node.value!r} in {source!r}")
        return {"op": "const", "value": node.value}

    if isinstance(node, ast.List | ast.Tuple):
        return {"op": "list", "items": [_compile(e, source) for e in node.elts]}

    raise RuleSyntaxError(f"{type(node).__name__} is not allowed in rule expressions: {source!r}")


def referenced_fields(node: Node) -> set[str]:
    """Every profile field the expression can touch. Used to build missing_fields."""
    op = node["op"]
    if op == "field":
        return {node["name"]}
    if op in ("and", "or"):
        return set().union(*(referenced_fields(a) for a in node["args"]))
    if op == "not":
        return referenced_fields(node["arg"])
    if op == "cmp":
        return referenced_fields(node["left"]) | referenced_fields(node["right"])
    if op == "list":
        if not node["items"]:
            return set()
        return set().union(*(referenced_fields(i) for i in node["items"]))
    return set()


# -------------------------------------------------------------------------- evaluate


def evaluate_node(node: Node, profile: dict[str, Any]) -> Ternary:
    """Interpret a compiled node under Kleene three-valued logic."""
    op = node["op"]

    if op == "and":
        seen_unknown = False
        for arg in node["args"]:
            value = evaluate_node(arg, profile)
            if value is False:
                return False  # False dominates AND, even with unknowns present
            if value is UNKNOWN:
                seen_unknown = True
        return UNKNOWN if seen_unknown else True

    if op == "or":
        seen_unknown = False
        for arg in node["args"]:
            value = evaluate_node(arg, profile)
            if value is True:
                return True  # True dominates OR
            if value is UNKNOWN:
                seen_unknown = True
        return UNKNOWN if seen_unknown else False

    if op == "not":
        value = evaluate_node(node["arg"], profile)
        return UNKNOWN if value is UNKNOWN else not value

    if op == "cmp":
        return _compare(node, profile)

    raise RuleSyntaxError(f"cannot evaluate node of type {op!r} as a condition")


def _operand(node: Node, profile: dict[str, Any]) -> Any:
    op = node["op"]
    if op == "field":
        return profile.get(node["name"])
    if op == "const":
        return node["value"]
    if op == "list":
        return [_operand(i, profile) for i in node["items"]]
    raise RuleSyntaxError(f"cannot use node of type {op!r} as an operand")


def _compare(node: Node, profile: dict[str, Any]) -> Ternary:
    left = _operand(node["left"], profile)
    right = _operand(node["right"], profile)
    operator = node["operator"]

    if operator in ("in", "not in"):
        if left is None or right is None:
            return UNKNOWN
        found = left in right
        return found if operator == "in" else not found

    # An unknown operand makes the comparison unknown, never False.
    if left is None or right is None:
        return UNKNOWN

    if operator == "==":
        return left == right
    if operator == "!=":
        return left != right

    # Ordered comparisons need comparable types; mixing them is a rule authoring bug.
    if isinstance(left, str) != isinstance(right, str):
        raise RuleSyntaxError(f"cannot compare {left!r} and {right!r} with {operator}")

    if operator == "<":
        return left < right
    if operator == "<=":
        return left <= right
    if operator == ">":
        return left > right
    if operator == ">=":
        return left >= right

    raise RuleSyntaxError(f"unknown comparison operator {operator!r}")
