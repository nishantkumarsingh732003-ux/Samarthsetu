"""Load and validate the YAML scheme definitions.

Validation is strict and happens at import time: an unknown field name, a malformed
expression, a duplicate rule id, or a `suggest_instead` pointing at a scheme that does
not exist all raise here rather than producing a wrong verdict at runtime.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from setu_rules.models import Family, Limits, OpenQuestion, Provenance, Rule, Scheme, Severity
from setu_rules.safe_eval import compile_expression, referenced_fields
from setu_rules.translations import load_bundles

SCHEMES_DIR = Path(__file__).resolve().parents[2] / "schemes"

_REQUIRED_TOP_LEVEL = ("code", "official_name", "family", "provenance", "limits", "rules")
_LIMIT_KEYS = (
    "min_project_cost",
    "max_project_cost",
    "max_loan_amount",
    "max_funding_pct",
    "interest_rate_min",
    "interest_rate_max",
    "tenure_months",
    "moratorium_months",
)


class RuleLoadError(ValueError):
    """Raised when a scheme file does not satisfy the DSL contract."""


def _require(data: dict[str, Any], key: str, where: str) -> Any:
    if key not in data:
        raise RuleLoadError(f"{where}: missing required key {key!r}")
    return data[key]


def _parse_rule(raw: dict[str, Any], where: str) -> Rule:
    rule_id = _require(raw, "id", where)
    where = f"{where} rule {rule_id}"

    severity_raw = _require(raw, "severity", where)
    try:
        severity = Severity(severity_raw)
    except ValueError as exc:
        raise RuleLoadError(f"{where}: severity must be HARD_BLOCK or SOFT_WARN") from exc

    when_source = _require(raw, "when", where)
    if not isinstance(when_source, str):
        raise RuleLoadError(f"{where}: `when` must be a string expression")
    compiled = compile_expression(when_source)

    messages = _require(raw, "message_i18n", where)
    if not isinstance(messages, dict) or "en" not in messages:
        raise RuleLoadError(f"{where}: message_i18n must be a mapping containing at least 'en'")

    satisfied = raw.get("satisfied_i18n") or {}
    if satisfied and "en" not in satisfied:
        raise RuleLoadError(f"{where}: satisfied_i18n must contain 'en' when present")

    # Languages beyond en/hi live in translations/<lang>.yaml, merged in here so the
    # rest of the engine sees one complete i18n map and knows nothing about bundles.
    merged_messages = dict(messages)
    merged_satisfied = dict(satisfied)
    for language, bundle in load_bundles().items():
        entry = bundle.rules.get(rule_id)
        if not entry:
            continue
        if entry.get("message"):
            merged_messages.setdefault(language, entry["message"])
        if entry.get("satisfied"):
            merged_satisfied.setdefault(language, entry["satisfied"])

    return Rule(
        id=rule_id,
        severity=severity,
        when_source=when_source,
        when=compiled,
        message_i18n=merged_messages,
        satisfied_i18n=merged_satisfied,
        suggest_instead=raw.get("suggest_instead"),
        fields=frozenset(referenced_fields(compiled)),
    )


def _parse_scheme(path: Path) -> Scheme:
    where = path.name
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuleLoadError(f"{where}: file must contain a YAML mapping")

    for key in _REQUIRED_TOP_LEVEL:
        _require(data, key, where)

    try:
        family = Family(data["family"])
    except ValueError as exc:
        raise RuleLoadError(f"{where}: unknown family {data['family']!r}") from exc

    prov = data["provenance"]
    provenance = Provenance(
        source=prov.get("source"),
        source_url=prov.get("source_url"),
        circular_ref=prov.get("circular_ref"),
        effective_from=str(prov["effective_from"]) if prov.get("effective_from") else None,
        last_verified_on=str(prov["last_verified_on"]) if prov.get("last_verified_on") else None,
        needs_verification=bool(prov.get("needs_verification", False)),
        verification_note=(prov.get("verification_note") or "").strip() or None,
        open_questions=tuple(
            OpenQuestion(field=q["field"], question=q["question"].strip())
            for q in (prov.get("open_questions") or [])
        ),
    )
    # CLAUDE.md rule 2: a figure without a source must be visibly unverified.
    if not provenance.needs_verification and not provenance.source_url:
        raise RuleLoadError(
            f"{where}: provenance has no source_url, so needs_verification must be true"
        )

    limits_raw = data["limits"]
    unknown_limits = set(limits_raw) - set(_LIMIT_KEYS)
    if unknown_limits:
        raise RuleLoadError(f"{where}: unknown limit key(s) {', '.join(sorted(unknown_limits))}")
    limits = Limits(**{k: limits_raw.get(k) for k in _LIMIT_KEYS})

    rules: list[Rule] = []
    seen: set[str] = set()
    for raw_rule in data["rules"]:
        rule = _parse_rule(raw_rule, where)
        if rule.id in seen:
            raise RuleLoadError(f"{where}: duplicate rule id {rule.id!r}")
        seen.add(rule.id)
        rules.append(rule)

    return Scheme(
        code=data["code"],
        official_name=data["official_name"],
        name_i18n=dict(data.get("name_i18n") or {}),
        family=family,
        provenance=provenance,
        limits=limits,
        rules=tuple(rules),
        pending_translations=tuple(data.get("pending_translations") or ()),
    )


@lru_cache(maxsize=1)
def load_schemes(directory: str | None = None) -> tuple[Scheme, ...]:
    """Parse every scheme file, sorted by code so iteration order is deterministic."""
    base = Path(directory) if directory else SCHEMES_DIR
    files = sorted(base.glob("*.yaml"))
    if not files:
        raise RuleLoadError(f"no scheme files found in {base}")

    schemes = tuple(sorted((_parse_scheme(p) for p in files), key=lambda s: s.code))

    codes = {s.code for s in schemes}
    if len(codes) != len(schemes):
        raise RuleLoadError("duplicate scheme code across files")

    for scheme in schemes:
        for rule in scheme.rules:
            target = rule.suggest_instead
            if target and target not in codes:
                raise RuleLoadError(
                    f"{scheme.code} rule {rule.id}: "
                    f"suggest_instead {target!r} is not a known scheme"
                )
    return schemes


@lru_cache(maxsize=1)
def rules_digest(directory: str | None = None) -> str:
    """Content hash of every scheme file.

    Pinned by a test, so any rule edit fails CI until someone bumps ENGINE_VERSION and
    records the new digest. That is the mechanism behind "policy changes are a data
    edit, reviewed like code".
    """
    base = Path(directory) if directory else SCHEMES_DIR
    digest = hashlib.sha256()
    for path in sorted(base.glob("*.yaml")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
