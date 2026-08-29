"""POST /api/v1/match — deterministic scheme eligibility.

Every call writes a `match_runs` row and an `audit_log` entry before returning, so a
verdict shown to a citizen can always be reproduced from storage.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from app.api.v1.deps import SessionDep
from app.schemas.match import MatchRequest, MatchResponse
from app.services import matching

router = APIRouter()


@router.post(
    "",
    response_model=MatchResponse,
    summary="Match a citizen profile to schemes",
    description=(
        "Runs the deterministic rule engine. No language model participates in the "
        "verdict. Missing facts produce NEED_MORE_INFO plus the single next question "
        "worth asking, never a refusal."
    ),
)
async def match(
    payload: MatchRequest,
    request: Request,
    session: SessionDep,
) -> MatchResponse:
    citizen_id: uuid.UUID | None = None
    if payload.citizen_id:
        try:
            citizen_id = uuid.UUID(payload.citizen_id)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, f"citizen_id is not a UUID: {exc}"
            ) from exc

    try:
        result = await matching.run_match(
            session,
            profile=payload.profile,
            language=payload.language,
            citizen_id=citizen_id,
            actor=request.client.host if request.client else "unknown",
        )
    except ValueError as exc:
        # The engine rejects unknown fields and out-of-vocabulary values. That is a
        # client error, and the message names the offending field.
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    await session.commit()
    return MatchResponse(**result)
