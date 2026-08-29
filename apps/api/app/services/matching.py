"""Eligibility matching, persisted for replay.

This module is a thin shell around `setu_rules`. It deliberately contains no
eligibility logic of its own: it forwards a profile to the deterministic engine,
writes the result to `match_runs`, and returns it.

If you ever find yourself tempted to adjust a verdict here — don't. Edit the YAML in
packages/rules/schemes/, bump ENGINE_VERSION, and let the golden tests show you what
moved.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MatchRun
from app.services import audit


async def run_match(
    session: AsyncSession,
    profile: dict[str, Any],
    language: str = "en",
    citizen_id: uuid.UUID | None = None,
    actor: str = "anonymous",
) -> dict[str, Any]:
    """Evaluate a profile and persist the run so the decision can be replayed."""
    from setu_rules import run as engine_run

    record = engine_run(profile, language=language)
    payload = record.to_dict()

    match_run = MatchRun(
        citizen_id=citizen_id,
        input_snapshot=payload["input_snapshot"],
        engine_version=payload["engine_version"],
        results=payload["results"],
    )
    session.add(match_run)
    await session.flush()

    await audit.record(
        session,
        actor=actor,
        action="MATCH_EVALUATED",
        entity="match_run",
        entity_id=str(match_run.id),
        meta={
            "engine_version": payload["engine_version"],
            "rules_digest": payload["rules_digest"],
            "language": language,
            "fields_supplied": sorted(profile),
            "top_scheme": payload["results"][0]["scheme_code"] if payload["results"] else None,
        },
    )

    payload["match_run_id"] = str(match_run.id)
    return payload
