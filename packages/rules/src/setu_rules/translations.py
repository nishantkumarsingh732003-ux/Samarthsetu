"""Per-language translation bundles.

Scheme YAML carries `en` and `hi` inline because those are the reviewed languages and
they sit next to the rules they describe. Everything else lives in
`packages/rules/translations/<lang>.yaml`, one file per language, so that:

  - adding a language is a file, not a code change in six places
  - a translator sees only strings, never rule syntax they could break
  - each language declares its own review status in one obvious place

**Status matters.** A `draft` bundle was written by a language model and has not been
read by a native speaker. These strings tell a citizen why they were refused government
credit, so `translation_status` travels all the way out to the API response — a UI can
badge unreviewed copy, and a deployment can refuse to serve it via
`SERVE_DRAFT_TRANSLATIONS=false`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

TRANSLATIONS_DIR = Path(__file__).resolve().parents[2] / "translations"

# Reviewed and maintained inline in the scheme files.
INLINE_LANGUAGES: frozenset[str] = frozenset({"en", "hi"})

# CLAUDE.md language priority order.
SUPPORTED_LANGUAGES: tuple[str, ...] = ("en", "hi", "mr", "bn", "ta", "te")

FALLBACK_LANGUAGE = "en"


@dataclass(frozen=True, slots=True)
class Bundle:
    language: str
    name_en: str
    name_native: str
    status: str  # "verified" | "draft"
    reviewed_by: str | None
    reviewed_on: str | None
    rules: dict[str, dict[str, str]] = field(default_factory=dict)
    fields: dict[str, str] = field(default_factory=dict)
    ui: dict[str, str] = field(default_factory=dict)
    approval_claims: tuple[str, ...] = ()
    cues: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def is_draft(self) -> bool:
        return self.status != "verified"


def _load_file(path: Path) -> Bundle:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Bundle(
        language=data["language"],
        name_en=data.get("language_name_en", data["language"]),
        name_native=data.get("language_name_native", data["language"]),
        status=data.get("status", "draft"),
        reviewed_by=data.get("reviewed_by"),
        reviewed_on=data.get("reviewed_on"),
        rules={k: dict(v) for k, v in (data.get("rules") or {}).items()},
        fields=dict(data.get("fields") or {}),
        ui=dict(data.get("ui") or {}),
        approval_claims=tuple(data.get("approval_claims") or ()),
        cues={k: tuple(v) for k, v in (data.get("cues") or {}).items()},
    )


@lru_cache(maxsize=1)
def load_bundles() -> dict[str, Bundle]:
    """Every translation bundle on disk, keyed by language code."""
    if not TRANSLATIONS_DIR.is_dir():
        return {}
    return {b.language: b for b in (_load_file(p) for p in sorted(TRANSLATIONS_DIR.glob("*.yaml")))}


def bundle_for(language: str) -> Bundle | None:
    return load_bundles().get(language)


def translation_status(language: str) -> str:
    """"verified" for a reviewed language, "draft" for machine-written, "fallback"
    when we have nothing and English will be served instead."""
    if language in INLINE_LANGUAGES:
        return "verified"
    bundle = bundle_for(language)
    if bundle is None:
        return "fallback"
    return "verified" if not bundle.is_draft else "draft"


def language_report() -> list[dict[str, Any]]:
    """What a reviewer needs: which languages exist, and which are trustworthy."""
    report = []
    for code in SUPPORTED_LANGUAGES:
        bundle = bundle_for(code)
        report.append(
            {
                "language": code,
                "name_native": bundle.name_native if bundle else code,
                "source": "inline" if code in INLINE_LANGUAGES else ("bundle" if bundle else None),
                "status": translation_status(code),
                "reviewed_by": bundle.reviewed_by if bundle else None,
                "rule_strings": len(bundle.rules) if bundle else None,
            }
        )
    return report
