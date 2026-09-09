"""A text-only entry point, shaped like WhatsApp.

The architectural claim this endpoint proves: the conversation is not a property of the
web app. `conversation.handle_turn` is the whole product, and the browser is one client
of it. A citizen on a Rs 1,500 feature phone with no data plan reaches the same
deterministic rule engine, the same six languages, and the same reference number — over
a channel that costs them nothing and needs no app install.

That is not a nice-to-have for this problem statement. The people furthest from a
Channel Partner branch are also the least likely to own a smartphone, and a service that
only reaches people who already have one has selected against exactly the citizens it was
funded to help.

**Rendering, not JSON.** WhatsApp has no cards, no chips and no buttons we can rely on,
so the same turn is flattened into numbered plain text: choices become "1) SC 2) ST",
and a bare digit in the next message is read as picking that option. That translation
lives here rather than in the orchestrator, because it is a property of the *channel*.

**Meta's webhook contract is honoured, not faked.** GET verifies the subscription with
`hub.challenge`; POST accepts Meta's real envelope shape. A `simulate` field is accepted
too so `/demo/whatsapp` can drive it without a Meta account, and the simulator marks
itself in the audit log so a stored conversation is never mistaken for a real one.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.deps import SessionDep
from app.core.config import settings
from app.services import audit, conversation, redaction
from app.services import session as session_store

logger = logging.getLogger(__name__)
router = APIRouter()

# Roughly two SMS-length screenfuls. A feature phone shows a few lines at a time and a
# citizen scrolling five paragraphs on a keypad has already given up.
# A digit-only reply picks a numbered choice. A property of the channel, not of the
# conversation, which is why it lives here.
DIGIT_REPLY = re.compile(r"^\s*([1-9])\s*$")

MAX_REPLY_CHARS = 900

LANGUAGE_WORDS: dict[str, str] = {
    "english": "en", "hindi": "hi", "हिंदी": "hi", "हिन्दी": "hi",
    "marathi": "mr", "मराठी": "mr",
    "bengali": "bn", "বাংলা": "bn",
    "tamil": "ta", "தமிழ்": "ta",
    "telugu": "te", "తెలుగు": "te",
}


class SimulatedMessage(BaseModel):
    """What `/demo/whatsapp` posts. Meta's own envelope is accepted too."""

    model_config = ConfigDict(extra="forbid")

    simulate: bool = True
    # A phone number in the simulator is a made-up string; it is hashed into a session
    # key and never stored (see `_session_key`).
    sender: str = Field(default="demo-user", max_length=64)
    text: str = Field(min_length=1, max_length=2000)
    language: str = Field(default="en", pattern="^(en|hi|mr|bn|ta|te)$")


class WhatsAppReply(BaseModel):
    to: str
    text: str
    language: str
    session_id: str
    stage: str
    # What a real WhatsApp send would have cost, so the channel's economics are visible.
    sms_segments: int
    finished: bool


def _session_key(sender: str) -> str:
    """A stable session id for a sender, without retaining the sender.

    A WhatsApp sender is a phone number. Hashing it with the ID salt means the same
    citizen resumes their conversation across messages while the number itself is never
    written down — the same posture the rest of the system takes towards identifiers.
    """
    from app.services.redaction import salted_hash

    return f"wa-{salted_hash(sender, settings.id_hash_salt)[:24]}"


def _detect_language(text: str, current: str) -> str:
    """Let someone switch language by naming it, in any of the six."""
    lowered = text.strip().lower()
    return LANGUAGE_WORDS.get(lowered, current)


def flatten(turn: dict[str, Any]) -> tuple[str, bool]:
    """Render one orchestrator turn as plain text. Returns (message, finished)."""
    stage = turn.get("stage")

    if stage in {"ASKING", "CONFIRMING"}:
        lines = [turn.get("question") or ""]
        choices = turn.get("question_choices")
        if choices:
            # Numbered so the reply can be a single keypress.
            lines.append("")
            lines.extend(f"{i}) {choice}" for i, choice in enumerate(choices, 1))
            lines.append("")
            lines.append("Reply with the number.")
        return "\n".join(line for line in lines if line is not None).strip(), False

    results = turn.get("results") or []
    if not results:
        return (
            "Sorry, we could not work that out. Tell us in a few words what you need "
            "the money for, and roughly how much."
        ), False

    lines: list[str] = []
    eligible = [r for r in results if r.get("verdict") in {"ELIGIBLE", "LIKELY_ELIGIBLE"}]
    shown = eligible or results[:1]

    for result in shown[:2]:
        # The official name, verbatim. Never translated (CLAUDE.md).
        lines.append(f"*{result['official_name']}*")
        for reason in (result.get("matched_because") or [])[:2]:
            lines.append(f"- {reason['message']}")
        if result.get("indicative_amount"):
            lines.append(f"Indicative: up to Rs {int(result['indicative_amount']):,}")
        lines.append("")

    if not eligible:
        blocked = results[0].get("blocked_because") or []
        if blocked:
            lines.append(f"Why not: {blocked[0]['message']}")
            lines.append("")

    lines.append("SamarthSetu does not lend. A Channel Partner decides.")
    lines.append(f"See partners near you: {settings.PUBLIC_WEB_URL}")

    message = "\n".join(lines).strip()
    if len(message) > MAX_REPLY_CHARS:
        message = message[: MAX_REPLY_CHARS - 3].rstrip() + "..."
    return message, True


async def _resolve_digit(session_id: str, text: str) -> str:
    """Turn "2" into the second option we offered.

    Reads the menu from the conversation session, which already records the last
    question and its choices for the web app's benefit. Keeping one source of truth
    matters more than it looks: a second, channel-local copy would drift the moment the
    orchestrator changed what it asks.
    """
    match = DIGIT_REPLY.match(text)
    if not match:
        return text

    convo = await session_store.load(session_id)
    choices = (convo.last_question or {}).get("choices") if convo else None
    if not choices:
        # No menu outstanding, so "2" is probably an amount. Leaving it alone lets the
        # extractor read it rather than inventing a menu that is no longer on screen.
        return text

    index = int(match.group(1)) - 1
    return str(choices[index]) if 0 <= index < len(choices) else text


async def _run_turn(
    session: SessionDep, sender: str, text: str, language: str, source: str
) -> WhatsAppReply:
    from app.services.notifications import sms_segments

    session_id = _session_key(sender)
    language = _detect_language(text, language)
    text = await _resolve_digit(session_id, text)

    # The exact same orchestrator the web app calls. No parallel implementation, so a
    # rule change cannot land on one channel and not the other.
    turn = await conversation.handle_turn(
        session, session_id=session_id, utterance=text, language=language
    )
    message, finished = flatten(turn)

    # Free text from an unauthenticated channel, echoed back to a phone. Mask before it
    # can carry an ID number anywhere.
    message = redaction.mask_text(message)
    segments, _ = sms_segments(message)

    await audit.record(
        session,
        actor=f"whatsapp:{session_id}",
        action="WHATSAPP_TURN",
        entity="conversation",
        entity_id=session_id,
        meta={
            "source": source,
            "language": language,
            "stage": turn.get("stage"),
            "finished": finished,
            "reply_segments": segments,
            # The citizen's own words are not stored here; the session already holds the
            # extracted facts, and an audit log is not a transcript.
            "utterance_length": len(text),
        },
    )
    await session.commit()

    return WhatsAppReply(
        to=sender,
        text=message,
        language=language,
        session_id=session_id,
        stage=str(turn.get("stage")),
        sms_segments=segments,
        finished=finished,
    )


@router.get(
    "/whatsapp",
    summary="Meta webhook verification",
    description="Answers the subscription challenge. Meta calls this once at setup.",
)
async def verify(
    mode: str = Query(default="", alias="hub.mode"),
    token: str = Query(default="", alias="hub.verify_token"),
    challenge: str = Query(default="", alias="hub.challenge"),
) -> Response:
    if not settings.WHATSAPP_VERIFY_TOKEN:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "No WHATSAPP_VERIFY_TOKEN is configured, so this webhook cannot be verified.",
        )
    if mode != "subscribe" or token != settings.WHATSAPP_VERIFY_TOKEN:
        # 403 with no detail: this endpoint is public and must not confirm the token.
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Verification failed.")
    return Response(content=challenge, media_type="text/plain")


@router.post(
    "/whatsapp",
    response_model=WhatsAppReply,
    summary="One conversational turn over a text-only channel",
    description=(
        "Runs the same orchestrator as the web app, rendered as plain numbered text for "
        "a feature phone. Accepts Meta's webhook envelope or the simulator's simpler "
        "shape, so the architecture can be demonstrated without a Meta account."
    ),
)
async def inbound(request: Request, session: SessionDep) -> WhatsAppReply:
    try:
        payload = await request.json()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Body must be JSON."
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Body must be a JSON object.")

    # --- the simulator's shape ---------------------------------------------------
    if payload.get("simulate") or "text" in payload:
        message = SimulatedMessage(**payload)
        return await _run_turn(
            session, message.sender, message.text, message.language, source="simulator"
        )

    # --- Meta's real envelope ----------------------------------------------------
    sender, text = _parse_meta_envelope(payload)
    if sender is None:
        # Meta sends status callbacks (delivered, read) through the same webhook. They
        # are not messages and must be acknowledged, not processed.
        logger.info("whatsapp.non_message_callback")
        raise HTTPException(
            status.HTTP_202_ACCEPTED, "Acknowledged; no inbound message in this payload."
        )

    return await _run_turn(session, sender, text, "en", source="meta")


def _parse_meta_envelope(payload: dict[str, Any]) -> tuple[str | None, str]:
    """Pull the first text message out of Meta's nested shape, or return (None, "")."""
    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    if message.get("type") != "text":
                        continue
                    body = (message.get("text") or {}).get("body", "")
                    if body:
                        return message.get("from"), body
    except (AttributeError, TypeError):
        logger.warning("whatsapp.malformed_envelope")
    return None, ""
