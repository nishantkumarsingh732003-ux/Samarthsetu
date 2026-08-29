"""POST /api/v1/conversation/turn — the conversational front door."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.deps import SessionDep
from app.services import conversation

router = APIRouter()

LANGUAGES = Literal["en", "hi", "mr", "bn", "ta", "te"]


class TurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str | None = Field(
        default=None, description="Omit to start a new conversation; the reply returns one."
    )
    utterance: str = Field(min_length=1, max_length=2000, examples=["mujhe 80 hazaar chahiye"])
    language: LANGUAGES = "en"


class TurnResponse(BaseModel):
    session_id: str
    language: str
    stage: str
    question: str | None
    question_field: str | None
    question_choices: list[str] | None = None
    resolves_rules: list[str] | None = None
    questions_asked: int
    max_questions: int
    profile: dict[str, Any]
    context: dict[str, Any] = Field(default_factory=dict)
    extraction: dict[str, Any]
    results: list[dict[str, Any]] | None
    explanations: list[dict[str, Any]] | None = None
    next_question: dict[str, Any] | None = None
    match_run_id: str | None = None
    engine_version: str | None = None
    rules_digest: str | None = None


@router.post(
    "/turn",
    response_model=TurnResponse,
    summary="One conversational turn",
    description=(
        "Extracts facts from the citizen's own words, merges them into the session "
        "profile, and runs the deterministic rule engine. A language model may read "
        "the message and may restate the verdict afterwards; it never participates in "
        "the verdict itself. An uncertain reading becomes a confirmation question "
        "rather than a silent write."
    ),
)
async def turn(payload: TurnRequest, session: SessionDep) -> TurnResponse:
    try:
        result = await conversation.handle_turn(
            session,
            session_id=payload.session_id,
            utterance=payload.utterance,
            language=payload.language,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc
    return TurnResponse(**result)
