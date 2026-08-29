"""Mirror the YAML rule pack into the `schemes` and `scheme_rules` tables.

`packages/rules/schemes/*.yaml` stays the single source of truth — the engine reads it
directly and never queries the database. These rows exist so that:

  - `partner_scheme_authorisations` has something to key on, and
  - the admin console can join applications and match runs to a scheme row.

Because the YAML is authoritative, this seeder overwrites rather than merges, and it
stamps `engine_version` so a row can be traced to the rule pack that produced it.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Scheme, SchemeRule
from app.models.enums import RuleSeverity, SchemeFamily


def _as_date(value: str | None) -> date | None:
    """Provenance dates travel as ISO strings through the engine; columns are DATE."""
    return date.fromisoformat(value) if value else None


async def seed_schemes(session: AsyncSession) -> str:
    from setu_rules import ENGINE_VERSION, load_schemes, rules_digest

    catalogue = load_schemes()
    created = updated = 0

    for spec in catalogue:
        limits = spec.limits
        prov = spec.provenance

        values: dict[str, Any] = {
            "official_name": spec.official_name,
            "name_i18n": dict(spec.name_i18n),
            "family": SchemeFamily(str(spec.family)),
            # The database column holds the LOAN cap, which is what an application is
            # sanctioned against. The project-cost band lives in the YAML and is
            # enforced by the engine, not by this table.
            "max_amount": limits.max_loan_amount,
            "max_funding_pct": limits.max_funding_pct,
            "interest_rate_min": limits.interest_rate_min,
            "interest_rate_max": limits.interest_rate_max,
            "tenure_months": limits.tenure_months,
            "moratorium_months": limits.moratorium_months,
            "source_url": prov.source_url,
            "circular_ref": prov.circular_ref,
            "effective_from": _as_date(prov.effective_from),
            "last_verified_on": _as_date(prov.last_verified_on),
            "needs_verification": prov.needs_verification,
            "is_active": True,
        }

        existing = (
            await session.execute(select(Scheme).where(Scheme.code == spec.code))
        ).scalar_one_or_none()

        if existing is None:
            scheme = Scheme(code=spec.code, **values)
            session.add(scheme)
            await session.flush()
            created += 1
        else:
            for key, value in values.items():
                setattr(existing, key, value)
            scheme = existing
            updated += 1

        # Rules are replaced wholesale: the YAML decides what exists.
        await session.execute(delete(SchemeRule).where(SchemeRule.scheme_id == scheme.id))
        for rule in spec.rules:
            session.add(
                SchemeRule(
                    scheme_id=scheme.id,
                    rule_id=rule.id,
                    expression={
                        "when": rule.when,
                        "when_source": rule.when_source,
                        "fields": sorted(rule.fields),
                        "engine_version": ENGINE_VERSION,
                    },
                    severity=RuleSeverity(str(rule.severity)),
                    message_i18n=dict(rule.message_i18n),
                    suggest_instead=rule.suggest_instead,
                )
            )

    rule_count = sum(len(s.rules) for s in catalogue)
    return (
        f"{created} created, {updated} updated, {rule_count} rules "
        f"(engine {ENGINE_VERSION}, digest {rules_digest()})"
    )
