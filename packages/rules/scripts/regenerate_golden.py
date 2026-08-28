"""Regenerate the golden snapshot and the compiled rule bundle.

Run this only after deliberately changing a rule, and read the resulting diff — it
shows exactly which citizens' verdicts moved.

    python packages/rules/scripts/regenerate_golden.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE_ROOT / "src"))
sys.path.insert(0, str(PACKAGE_ROOT / "tests"))

from test_golden import build_snapshot  # noqa: E402

from setu_rules import ENGINE_VERSION, load_schemes, rules_digest  # noqa: E402
from setu_rules.profile import FIELDS  # noqa: E402


def write_golden() -> Path:
    target = PACKAGE_ROOT / "tests" / "golden" / "expected.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(build_snapshot(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return target


def write_bundle() -> Path:
    """Compile the YAML into the JSON bundle the TypeScript engine consumes.

    The web app never parses YAML: it reads this precompiled tree, so both runtimes
    interpret the identical expression AST and cannot drift.
    """
    schemes = []
    for scheme in load_schemes():
        schemes.append(
            {
                "code": scheme.code,
                "official_name": scheme.official_name,
                "name_i18n": scheme.name_i18n,
                "family": str(scheme.family),
                "provenance": scheme.provenance.to_dict(),
                "limits": {
                    "min_project_cost": scheme.limits.min_project_cost,
                    "max_project_cost": scheme.limits.max_project_cost,
                    "max_loan_amount": scheme.limits.max_loan_amount,
                    "max_funding_pct": scheme.limits.max_funding_pct,
                    "interest_rate_min": scheme.limits.interest_rate_min,
                    "interest_rate_max": scheme.limits.interest_rate_max,
                    "tenure_months": scheme.limits.tenure_months,
                    "moratorium_months": scheme.limits.moratorium_months,
                },
                "rules": [
                    {
                        "id": rule.id,
                        "severity": str(rule.severity),
                        "when": rule.when,
                        "when_source": rule.when_source,
                        "message_i18n": rule.message_i18n,
                        "satisfied_i18n": rule.satisfied_i18n,
                        "suggest_instead": rule.suggest_instead,
                        "fields": sorted(rule.fields),
                    }
                    for rule in scheme.rules
                ],
            }
        )

    # The field contract ships in the bundle too, so the TypeScript side never
    # hand-maintains a second copy of the question text or the tie-break priorities.
    fields = {
        name: {
            "name": field.name,
            "kind": field.kind,
            "choices": list(field.choices) if field.choices else None,
            "question_i18n": dict(field.question_i18n),
            "priority": field.priority,
        }
        for name, field in sorted(FIELDS.items())
    }

    bundle = {
        "engine_version": ENGINE_VERSION,
        "rules_digest": rules_digest(),
        "fields": fields,
        "schemes": schemes,
    }
    target = PACKAGE_ROOT / "dist" / "rules.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(bundle, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return target


def main() -> None:
    golden = write_golden()
    bundle = write_bundle()
    print(f"engine_version : {ENGINE_VERSION}")
    print(f"rules_digest   : {rules_digest()}")
    print(f"golden         : {golden.relative_to(PACKAGE_ROOT)}")
    print(f"bundle         : {bundle.relative_to(PACKAGE_ROOT)}")
    print()
    print("If the digest changed, update PINNED_RULES_DIGEST and bump ENGINE_VERSION.")


if __name__ == "__main__":
    main()
