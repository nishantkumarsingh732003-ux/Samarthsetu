"""Which documents this citizen actually needs.

A generic list of every document any applicant might need is what a citizen already
gets from a government website, and it is why they arrive at a branch with the wrong
folder. This narrows the list to the scheme they matched, the partner type they were
routed to, and the facts they gave us — and states why each one is wanted, because a
document you understand the purpose of is one you are more likely to bring.

`profile_when` reuses the same whitelisted AST evaluator the eligibility rules use, so
a typo in a condition fails at load time rather than silently including or dropping a
document.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from setu_rules.models import Provenance
from setu_rules.safe_eval import compile_expression, evaluate_node
from setu_rules.translations import FALLBACK_LANGUAGE

DOCUMENTS_DIR = Path(__file__).resolve().parents[2] / "documents"


class DocumentLoadError(ValueError):
    """Raised when the checklist file does not satisfy its contract."""


@dataclass(frozen=True, slots=True)
class DocumentSpec:
    id: str
    name_i18n: dict[str, str]
    why_i18n: dict[str, str]
    issued_by: str | None
    validity_months: int | None
    validity_is_practice_not_rule: bool
    contains_government_id: bool
    families: tuple[str, ...]
    partner_types: tuple[str, ...]
    profile_when: dict[str, Any] | None
    profile_when_source: str | None

    def name(self, language: str) -> str:
        return self.name_i18n.get(language) or self.name_i18n[FALLBACK_LANGUAGE]

    def why(self, language: str) -> str:
        return self.why_i18n.get(language) or self.why_i18n[FALLBACK_LANGUAGE]


@dataclass(frozen=True, slots=True)
class RequiredDocument:
    id: str
    name: str
    why: str
    issued_by: str | None
    validity_months: int | None
    validity_is_practice_not_rule: bool
    contains_government_id: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "why": self.why,
            "issued_by": self.issued_by,
            "validity_months": self.validity_months,
            "validity_is_practice_not_rule": self.validity_is_practice_not_rule,
            "contains_government_id": self.contains_government_id,
        }


def _parse(raw: dict[str, Any]) -> DocumentSpec:
    doc_id = raw.get("id")
    if not doc_id:
        raise DocumentLoadError("a document entry has no id")

    for key in ("name_i18n", "why_i18n"):
        block = raw.get(key)
        if not isinstance(block, dict) or FALLBACK_LANGUAGE not in block:
            raise DocumentLoadError(f"{doc_id}: {key} must contain at least 'en'")

    applies = raw.get("applies_to") or {}
    condition = applies.get("profile_when")

    return DocumentSpec(
        id=doc_id,
        name_i18n=dict(raw["name_i18n"]),
        why_i18n=dict(raw["why_i18n"]),
        issued_by=raw.get("issued_by"),
        validity_months=raw.get("validity_months"),
        validity_is_practice_not_rule=bool(raw.get("validity_is_practice_not_rule", False)),
        contains_government_id=bool(raw.get("contains_government_id", False)),
        families=tuple(applies.get("families") or ()),
        partner_types=tuple(applies.get("partner_types") or ()),
        # Compiled at load: an unknown field name is a load-time error, not a silent
        # miss that drops a document from a citizen's list.
        profile_when=compile_expression(condition) if condition else None,
        profile_when_source=condition,
    )


@lru_cache(maxsize=1)
def load_documents(directory: str | None = None) -> tuple[tuple[DocumentSpec, ...], Provenance]:
    base = Path(directory) if directory else DOCUMENTS_DIR
    path = base / "checklist.yaml"
    if not path.is_file():
        raise DocumentLoadError(f"no checklist.yaml in {base}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    prov = data.get("provenance") or {}
    provenance = Provenance(
        source=prov.get("source"),
        source_url=prov.get("source_url"),
        circular_ref=prov.get("circular_ref"),
        effective_from=None,
        last_verified_on=str(prov["last_verified_on"]) if prov.get("last_verified_on") else None,
        needs_verification=bool(prov.get("needs_verification", True)),
        verification_note=(prov.get("verification_note") or "").strip() or None,
    )
    if not provenance.needs_verification and not provenance.source_url:
        raise DocumentLoadError("checklist has no source_url, so needs_verification must be true")

    specs = tuple(_parse(entry) for entry in (data.get("documents") or ()))
    if len({s.id for s in specs}) != len(specs):
        raise DocumentLoadError("duplicate document id in checklist.yaml")
    return specs, provenance


def checklist_digest(directory: str | None = None) -> str:
    """Content hash, so a changed checklist is visible the way a rule change is."""
    base = Path(directory) if directory else DOCUMENTS_DIR
    return hashlib.sha256((base / "checklist.yaml").read_bytes()).hexdigest()[:16]


def required_documents(
    family: str,
    partner_type: str | None = None,
    profile: dict[str, Any] | None = None,
    language: str = FALLBACK_LANGUAGE,
) -> list[RequiredDocument]:
    """The documents this citizen needs, in checklist order.

    A `profile_when` condition that cannot be decided yet (UNKNOWN, because the citizen
    has not told us the fact it depends on) **includes** the document. Over-listing
    costs a citizen one extra piece of paper; under-listing costs them a second trip to
    the branch, which is the failure this project exists to prevent.
    """
    profile = profile or {}
    specs, _ = load_documents()
    out: list[RequiredDocument] = []

    for spec in specs:
        if spec.families and family not in spec.families:
            continue
        if (
            spec.partner_types
            and partner_type is not None
            and partner_type not in spec.partner_types
        ):
            continue
        if spec.profile_when is not None:
            outcome = evaluate_node(spec.profile_when, profile)
            if outcome is False:
                continue
            # UNKNOWN falls through: include it.

        out.append(
            RequiredDocument(
                id=spec.id,
                name=spec.name(language),
                why=spec.why(language),
                issued_by=spec.issued_by,
                validity_months=spec.validity_months,
                validity_is_practice_not_rule=spec.validity_is_practice_not_rule,
                contains_government_id=spec.contains_government_id,
            )
        )
    return out


def checklist_provenance() -> Provenance:
    return load_documents()[1]
