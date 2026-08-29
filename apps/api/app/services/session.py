"""Conversation session state in Redis, 24h TTL.

CLAUDE.md rule 4: no PII beyond masked fields. What is stored is the *eligibility
profile* — income band, category, sector, amount — which are the facts the rule engine
needs and which identify nobody on their own.

What is deliberately NOT stored:
  - the citizen's raw words, which routinely contain a name, a village, a phone number
    or an Aadhaar number spoken aloud
  - anything that could reconstruct them

The turn log keeps only which fields each turn established and which question was
asked back, which is enough to debug a conversation and audit a decision without
retaining what the person said.
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core import cache

logger = logging.getLogger(__name__)

SESSION_TTL_SECONDS = 24 * 60 * 60
MAX_QUESTIONS = 6

_KEY_PREFIX = "setu:session:"


def key_for(session_id: str) -> str:
    return f"{_KEY_PREFIX}{session_id}"


@dataclass(slots=True)
class Session:
    session_id: str
    language: str = "en"
    profile: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    questions_asked: list[str] = field(default_factory=list)
    turns: list[dict[str, Any]] = field(default_factory=list)
    pending_confirmation: dict[str, Any] | None = None

    @property
    def question_count(self) -> int:
        return len(self.questions_asked)

    @property
    def at_question_limit(self) -> bool:
        return self.question_count >= MAX_QUESTIONS

    def record_turn(self, established: list[str], question_field: str | None) -> None:
        """Log the shape of a turn, never its content."""
        self.turns.append(
            {
                "turn": len(self.turns) + 1,
                "fields_established": established,
                "question_asked": question_field,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "language": self.language,
            "profile": self.profile,
            "context": self.context,
            "questions_asked": self.questions_asked,
            "turns": self.turns,
            "pending_confirmation": self.pending_confirmation,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Session:
        return cls(
            session_id=data["session_id"],
            language=data.get("language", "en"),
            profile=data.get("profile", {}),
            context=data.get("context", {}),
            questions_asked=data.get("questions_asked", []),
            turns=data.get("turns", []),
            pending_confirmation=data.get("pending_confirmation"),
        )


async def load(session_id: str) -> Session | None:
    try:
        raw = await cache.get_client().get(key_for(session_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("session load failed, starting fresh: %s", exc)
        return None
    if raw is None:
        return None
    try:
        return Session.from_dict(json.loads(raw))
    except (json.JSONDecodeError, KeyError):
        logger.warning("discarding malformed session %s", session_id)
        return None


async def save(session: Session) -> None:
    try:
        await cache.get_client().set(
            key_for(session.session_id),
            json.dumps(session.to_dict(), default=str),
            ex=SESSION_TTL_SECONDS,
        )
    except Exception as exc:  # noqa: BLE001 - a lost session must not fail the turn
        logger.warning("session save failed: %s", exc)


async def load_or_create(session_id: str | None, language: str = "en") -> Session:
    if session_id:
        existing = await load(session_id)
        if existing is not None:
            existing.language = language or existing.language
            return existing
    return Session(session_id=session_id or str(uuid.uuid4()), language=language)


async def delete(session_id: str) -> None:
    try:
        await cache.get_client().delete(key_for(session_id))
    except Exception as exc:  # noqa: BLE001
        logger.warning("session delete failed: %s", exc)
