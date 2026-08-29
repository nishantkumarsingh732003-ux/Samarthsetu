"""Append-only audit trail.

CLAUDE.md rule 4 requires a full log of who read what. Every read or write that touches
citizen data or produces a decision writes a row here. Rows are never updated or
deleted.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record(
    session: AsyncSession,
    *,
    actor: str,
    action: str,
    entity: str,
    entity_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        actor=actor,
        action=action,
        entity=entity,
        entity_id=entity_id,
        meta=meta or {},
    )
    session.add(entry)
    return entry
