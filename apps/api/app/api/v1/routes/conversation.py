"""POST /api/v1/conversation/turn — the conversational front door."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.v1.deps import CitizenUser, SessionDep
from app.services import assistant, audit, conversation

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


class AskTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["citizen", "assistant"]
    text: str = Field(max_length=4000)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=1000)
    language: LANGUAGES = "en"
    history: list[AskTurn] = Field(
        default_factory=list,
        max_length=20,
        description=(
            "Recent turns, oldest first, so a follow-up like 'and the interest?' "
            "resolves. The server keeps the last few; the cap is here so one client "
            "cannot post an unbounded transcript."
        ),
    )


class AskResponse(BaseModel):
    answer: str
    rule_ids: list[str] = Field(default_factory=list)
    action: str | None = None
    action_scheme_code: str | None = None
    grounded: bool
    """False when no model was configured and the deterministic reply was used."""


@router.post(
    "/ask",
    response_model=AskResponse,
    summary="Answer a citizen's question from the rule pack and their own record",
    description=(
        "Assembles a context pack — the published schemes and their rules, the "
        "citizen's profile, the engine's own verdicts with the rule ids that produced "
        "them, and their applications — and has a language model answer from it and "
        "nothing else. "
        "The model does not decide eligibility. Verdicts in the pack come from the "
        "deterministic engine; the model restates them and cites the rule ids. It may "
        "propose one next step, which the client renders as a button — it never acts."
    ),
)
async def ask(
    payload: AskRequest,
    user: CitizenUser,
    session: SessionDep,
    request: Request,
) -> AskResponse:
    # Imported here rather than at module scope: the citizen routes own the profile
    # loading and the match cache, and importing them at the top would make this module
    # part of that cycle.
    from app.api.v1.routes.citizen import _load, matches
    from app.api.v1.routes.citizen import applications as my_applications
    from app.api.v1.routes.schemes import catalogue
    from app.api.v1.routes.schemes import detail as scheme_detail
    from app.services import citizen_accounts

    citizen, profile = await _load(session, user)

    run = await matches(user=user, session=session, request=request, language=payload.language)
    pack = await catalogue(session=session, language=payload.language)

    # Their live applications, because half the questions this page exists to answer are
    # about one — "what documents do I still need?", "where has it got to?". Without
    # these the pack has no way to answer, the prompt correctly refuses to guess, and the
    # assistant says it does not know about the citizen's own application.
    raised = await my_applications(user=user, session=session)

    # Rules and documents live on the detail projection, not the summary, and the pack
    # is what makes an answer citable — so each scheme is fetched in full.
    schemes = [
        (await scheme_detail(
            code=summary.code, session=session, language=payload.language
        )).model_dump()
        for summary in pack.schemes
    ]

    context = assistant.build_context(
        profile=citizen_accounts.engine_profile(citizen, profile),
        schemes=schemes,
        results=[r if isinstance(r, dict) else r.model_dump() for r in run.results],
        applications=[a.model_dump() for a in raised],
    )

    result = await assistant.answer(
        payload.question,
        context,
        payload.language,
        history=[turn.model_dump() for turn in payload.history],
    )

    # CLAUDE.md rule 4: a full log of who read what. An assistant answer is a read of
    # this citizen's own verdicts, and the question is kept so an answer can be
    # explained after the fact.
    await audit.record(
        session,
        actor=user.email,
        action="ASSISTANT_ANSWERED",
        entity="citizen",
        entity_id=str(citizen.id),
        meta={
            "question": payload.question[:500],
            "grounded": result.grounded,
            "rule_ids": result.rule_ids,
            "action": result.action,
        },
    )
    await session.commit()

    return AskResponse(
        answer=result.text,
        rule_ids=result.rule_ids,
        action=result.action,
        action_scheme_code=result.action_scheme_code,
        grounded=result.grounded,
    )
