"""Conversation orchestrator.

One turn is: extract facts -> merge into the session profile -> run the deterministic
rule engine -> either ask the single most useful remaining question, or return the
ranked schemes.

The ordering is the guarantee. Extraction runs before the engine and only produces
candidate facts; explanation runs after the engine and only restates its output.
Nothing a language model emits reaches the verdict, which is why the same profile
reached by conversation and the same profile passed directly to the engine return
identical results — asserted in tests/test_conversation.py.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services import explanation, extraction, matching
from app.services import session as session_store
from app.services.session import MAX_QUESTIONS, Session

AFFIRMATIVE = (
    "yes", "yeah", "yep", "correct", "right", "sahi", "haan", "ha", "ji", "thik",
    "हाँ", "हां", "सही", "जी", "ठीक",
)
NEGATIVE = ("no", "nope", "wrong", "galat", "nahi", "nahin", "नहीं", "गलत")


def _is_affirmative(utterance: str) -> bool | None:
    text = utterance.strip().lower()
    if any(text.startswith(w) or f" {w}" in f" {text}" for w in NEGATIVE):
        return False
    if any(text.startswith(w) or f" {w}" in f" {text}" for w in AFFIRMATIVE):
        return True
    return None


def _localise_question(question: dict[str, Any], language: str) -> str:
    texts = question.get("question_i18n", {})
    return texts.get(language) or texts.get("en") or question.get("field", "")


async def handle_turn(
    db: AsyncSession,
    session_id: str | None,
    utterance: str,
    language: str = "en",
) -> dict[str, Any]:
    """Process one conversational turn and return what the citizen should see next."""
    convo = await session_store.load_or_create(session_id, language)
    established: list[str] = []

    # --- 1. a pending confirmation takes precedence over fresh extraction ----------
    if convo.pending_confirmation:
        answer = _is_affirmative(utterance)
        pending = convo.pending_confirmation
        if answer is True:
            _write(convo, pending["field"], pending["value"])
            established.append(pending["field"])
            convo.pending_confirmation = None
        elif answer is False:
            convo.pending_confirmation = None
        # An ambiguous reply falls through to normal extraction; if the citizen
        # restated the value we will pick it up below.

    # --- 2. extract facts ----------------------------------------------------------
    result = await extraction.extract(utterance, language, convo.profile)

    for item in result.accepted:
        _write(convo, item.field, item.value)
        established.append(item.field)

    # --- 3. an uncertain reading becomes a question, never a silent write ----------
    if result.needs_confirmation and not convo.pending_confirmation:
        candidate = max(result.needs_confirmation, key=lambda f: f.confidence)
        convo.pending_confirmation = {
            "field": candidate.field,
            "value": candidate.value,
            "confidence": candidate.confidence,
        }
        convo.record_turn(established, f"confirm:{candidate.field}")
        await session_store.save(convo)
        return {
            "session_id": convo.session_id,
            "language": language,
            "stage": "CONFIRMING",
            "question": extraction.confirmation_question(candidate, language),
            "question_field": candidate.field,
            "questions_asked": convo.question_count,
            "max_questions": MAX_QUESTIONS,
            "profile": dict(convo.profile),
            "extraction": result.to_dict(),
            "results": None,
            "next_question": None,
        }

    # --- 4. the deterministic engine decides --------------------------------------
    from setu_rules import next_best_question

    engine_payload = await matching.run_match(
        db,
        profile=dict(convo.profile),
        language=language,
        citizen_id=None,
        actor=f"session:{convo.session_id}",
    )
    await db.commit()

    # Never ask the same thing twice while the citizen is still talking to us.
    question = next_best_question(dict(convo.profile), exclude=set(convo.questions_asked))

    # --- 5. ask, or answer ---------------------------------------------------------
    if question is not None and not convo.at_question_limit:
        payload = question.to_dict()
        convo.questions_asked.append(payload["field"])
        convo.record_turn(established, payload["field"])
        await session_store.save(convo)
        return {
            "session_id": convo.session_id,
            "language": language,
            "stage": "ASKING",
            "question": _localise_question(payload, language),
            "question_field": payload["field"],
            "question_choices": payload.get("choices"),
            "resolves_rules": payload.get("resolves_rules"),
            "questions_asked": convo.question_count,
            "max_questions": MAX_QUESTIONS,
            "profile": dict(convo.profile),
            "extraction": result.to_dict(),
            "results": None,
            "next_question": payload,
        }

    convo.record_turn(established, None)
    await session_store.save(convo)

    explanations = [
        await explanation.explain(item, language) for item in engine_payload["results"]
    ]

    return {
        "session_id": convo.session_id,
        "language": language,
        "stage": "DECIDED" if question is None else "QUESTION_LIMIT_REACHED",
        "question": None,
        "question_field": None,
        "questions_asked": convo.question_count,
        "max_questions": MAX_QUESTIONS,
        "profile": dict(convo.profile),
        "context": dict(convo.context),
        "extraction": result.to_dict(),
        "match_run_id": engine_payload["match_run_id"],
        "engine_version": engine_payload["engine_version"],
        "rules_digest": engine_payload["rules_digest"],
        "results": engine_payload["results"],
        "explanations": explanations,
        "next_question": None,
    }


def _write(convo: Session, name: str, value: Any) -> None:
    """Route a fact to the eligibility profile or the routing context."""
    if name in extraction.CONTEXT_FIELDS:
        convo.context[name] = value
    else:
        convo.profile[name] = value


def new_session_id() -> str:
    return str(uuid.uuid4())
