"""Applications: submit, track, upload documents, advance status.

The submission path is ordered so that the DPDP guarantees are structural rather than
remembered: consent is written first, the government ID is masked inside the citizen
service, and the reference number is issued last, once there is something to reference.

Document upload redacts before it stores. `documents.analyse` returns the bytes that may
be written, and raises if it could not mask what it found — so the storage call below
has no path that could write an original.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.deps import SessionDep
from app.core.config import settings
from app.models import Application, ChannelPartner, Document, MatchRun, Scheme
from app.models.enums import ApplicationStatus
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    ChecklistResponse,
    DocumentOut,
    DocumentUploadResponse,
    RequiredDocumentOut,
    TimelineEntryOut,
    TransitionRequest,
)
from app.services import applications, audit, citizens, documents, redaction, storage

router = APIRouter()


def _actor(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _as_uuid(value: str | None, field: str) -> uuid.UUID | None:
    if not value:
        return None
    try:
        return uuid.UUID(value)
    except ValueError as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, f"{field} is not a UUID"
        ) from exc


def _document_out(doc: Document) -> DocumentOut:
    extract = doc.ocr_extract or {}
    return DocumentOut(
        id=str(doc.id),
        doc_type=doc.doc_type,
        validation_status=str(doc.validation_status),
        redaction_applied=doc.redaction_applied,
        warnings=extract.get("warnings", []),
        detected_type=extract.get("detected_type"),
        uploaded_at=doc.created_at.isoformat() if doc.created_at else None,
    )


async def _load(session: AsyncSession, reference_no: str) -> Application:
    result = await session.execute(
        select(Application)
        .options(selectinload(Application.documents))
        .where(Application.reference_no == reference_no)
    )
    application = result.scalar_one_or_none()
    if application is None:
        # Deliberately identical wording whether the reference never existed or belongs
        # to someone else: a 404 that distinguishes the two is a reference-number oracle.
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No application with that reference number.")
    return application


async def _engine_version(session: AsyncSession, match_run_id: uuid.UUID | None) -> str | None:
    """Take the engine version from the recorded run, not from whatever is live now.

    An application must remember the rules that produced it. Reading the current
    `ENGINE_VERSION` here would quietly rewrite history the next time the YAML changes.
    """
    if match_run_id is None:
        return None
    run = (
        await session.execute(select(MatchRun).where(MatchRun.id == match_run_id))
    ).scalar_one_or_none()
    return run.engine_version if run else None


async def _build_out(
    session: AsyncSession, application: Application, language: str
) -> ApplicationOut:
    from setu_rules.documents import checklist_provenance, required_documents

    scheme = (
        await session.execute(select(Scheme).where(Scheme.id == application.scheme_id))
    ).scalar_one()

    partner_block = None
    partner_type: str | None = None
    if application.partner_id:
        partner = (
            await session.execute(
                select(ChannelPartner).where(ChannelPartner.id == application.partner_id)
            )
        ).scalar_one_or_none()
        if partner is not None:
            partner_type = str(partner.type)
            partner_block = {
                "id": str(partner.id),
                "name": partner.name,
                "type": str(partner.type),
                "address": partner.address,
                "district": partner.district,
                "state": partner.state,
                "contact": partner.contact,
            }

    uploaded_types = {doc.doc_type for doc in application.documents}
    required = required_documents(
        family=str(scheme.family), partner_type=partner_type, profile={}, language=language
    )
    required_out = [
        RequiredDocumentOut(**doc.to_dict(), uploaded=doc.id in uploaded_types) for doc in required
    ]

    history = application.status_history or []
    return ApplicationOut(
        reference_no=application.reference_no,
        status=str(application.status),
        scheme_code=scheme.code,
        # Official name verbatim, never machine-translated (CLAUDE.md).
        scheme_name=scheme.official_name,
        family=str(scheme.family),
        partner=partner_block,
        amount_requested=float(application.amount_requested)
        if application.amount_requested is not None
        else None,
        submitted_at=application.created_at.isoformat() if application.created_at else None,
        engine_version=application.engine_version,
        match_run_id=str(application.match_run_id) if application.match_run_id else None,
        timeline=[TimelineEntryOut(**entry) for entry in history],
        documents=[_document_out(doc) for doc in application.documents],
        required_documents=required_out,
        documents_outstanding=sum(1 for doc in required_out if not doc.uploaded),
        checklist_needs_verification=checklist_provenance().needs_verification,
    )


@router.post(
    "",
    response_model=ApplicationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Submit an application to a Channel Partner",
    description=(
        "Records consent, stores the applicant with their government ID masked to the "
        "last four digits plus a salted hash, and issues a quotable reference number. "
        "SETU never disburses; this is a routed introduction to a Channel Partner."
    ),
)
async def submit(
    payload: ApplicationCreate,
    request: Request,
    session: SessionDep,
) -> ApplicationOut:
    # Nothing the citizen typed reaches storage before this check.
    try:
        consent = await citizens.record_consent(
            session,
            granted=payload.consent.granted,
            purpose=payload.consent.purpose,
            ip=_actor(request),
        )
    except citizens.ConsentRequired as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(exc)) from exc

    try:
        citizen = await citizens.create_citizen(
            session,
            consent=consent,
            display_name=payload.applicant.display_name,
            phone=payload.applicant.phone,
            gov_id_type=payload.applicant.gov_id_type,
            gov_id=payload.applicant.gov_id,
            district=payload.applicant.district,
            state=payload.applicant.state,
            preferred_language=payload.applicant.preferred_language,
            actor=_actor(request),
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(exc)) from exc

    match_run_id = _as_uuid(payload.match_run_id, "match_run_id")
    try:
        application = await applications.create_application(
            session,
            citizen_id=citizen.id,
            scheme_code=payload.scheme_code,
            partner_id=_as_uuid(payload.partner_id, "partner_id"),
            amount_requested=payload.amount_requested,
            match_run_id=match_run_id,
            engine_version=await _engine_version(session, match_run_id),
            actor=_actor(request),
        )
    except applications.ApplicationNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from exc

    await session.refresh(application, ["documents"])
    out = await _build_out(session, application, payload.language)
    await session.commit()
    return out


@router.get(
    "/{reference_no}",
    response_model=ApplicationOut,
    summary="Track an application",
    description=(
        "The citizen-facing tracking view: status timeline, the partner handling it, "
        "and which documents are still outstanding. Returns no personal data."
    ),
)
async def track(
    reference_no: str,
    request: Request,
    session: SessionDep,
    language: str = "en",
) -> ApplicationOut:
    application = await _load(session, reference_no)
    await audit.record(
        session,
        actor=_actor(request),
        action="APPLICATION_VIEWED",
        entity="application",
        entity_id=str(application.id),
        meta={"reference_no": reference_no},
    )
    out = await _build_out(session, application, language)
    await session.commit()
    return out


@router.post(
    "/{reference_no}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a supporting document",
    description=(
        "OCR runs locally; the file never leaves this machine. Any government ID is "
        "masked in the extracted text and painted over in the stored image before the "
        "file is written. Validation produces warnings, never a block — a citizen is "
        "told their certificate looks expired, and decides for themselves."
    ),
)
async def upload_document(
    reference_no: str,
    request: Request,
    session: SessionDep,
    file: Annotated[UploadFile, File()],
    doc_type: Annotated[str, Form()],
    validity_months: Annotated[int | None, Form()] = None,
) -> DocumentUploadResponse:
    application = await _load(session, reference_no)
    data = await file.read()

    try:
        result, storable = documents.analyse(
            data,
            content_type=file.content_type or "application/octet-stream",
            doc_type=doc_type,
            salt=settings.id_hash_salt,
            validity_months=validity_months,
        )
    except documents.UnsupportedUpload as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except documents.RedactionUnavailable as exc:
        # 503, not 400: the citizen did nothing wrong, and retrying later may work.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(exc)) from exc

    payload = result.to_dict()
    # Third defence. If either of the first two has a bug, this refuses the write.
    redaction.assert_no_government_id(payload, "document upload")

    document = Document(
        application_id=application.id,
        doc_type=doc_type,
        storage_key="",  # set below, once the row has an id
        ocr_extract=payload,
        validation_status=result.validation_status,
        redaction_applied=result.redaction_applied,
    )
    session.add(document)
    await session.flush()

    document.storage_key = storage.write(
        storage.build_key(application.id, document.id), storable
    )

    await audit.record(
        session,
        actor=_actor(request),
        action="DOCUMENT_UPLOADED",
        entity="document",
        entity_id=str(document.id),
        meta={
            "reference_no": reference_no,
            "doc_type": doc_type,
            "validation_status": str(result.validation_status),
            "redaction_applied": result.redaction_applied,
            "government_ids_masked": len(result.masked_ids),
            "warnings": [w.code for w in result.warnings],
        },
    )
    await session.commit()

    return DocumentUploadResponse(
        document=_document_out(document),
        extract=result.extract,
        masked_ids=result.masked_ids,
    )


@router.post(
    "/{reference_no}/transition",
    response_model=ApplicationOut,
    summary="Advance an application along its lifecycle",
    description=(
        "Partner-side status update. Illegal transitions are refused: a partner cannot "
        "sanction an application it never acknowledged."
    ),
)
async def transition(
    reference_no: str,
    payload: TransitionRequest,
    session: SessionDep,
    language: str = "en",
) -> ApplicationOut:
    application = await _load(session, reference_no)
    try:
        await applications.transition(
            session,
            application,
            ApplicationStatus(payload.to_status),
            actor=payload.actor,
            reason=payload.reason,
        )
    except applications.IllegalTransition as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc

    out = await _build_out(session, application, language)
    await session.commit()
    return out


checklist_router = APIRouter()


@checklist_router.get(
    "/checklist",
    response_model=ChecklistResponse,
    summary="The documents this citizen actually needs",
    description=(
        "Narrowed to the scheme family, the partner type, and the facts already given, "
        "with a reason for each document. A condition that cannot yet be decided "
        "includes the document: an extra sheet of paper beats a second trip."
    ),
)
async def checklist(
    family: str,
    partner_type: str | None = None,
    language: str = "en",
) -> ChecklistResponse:
    from setu_rules.documents import (
        checklist_digest,
        checklist_provenance,
        required_documents,
    )

    docs = required_documents(family=family, partner_type=partner_type, language=language)
    provenance = checklist_provenance()
    return ChecklistResponse(
        family=family,
        partner_type=partner_type,
        language=language,
        documents=[RequiredDocumentOut(**doc.to_dict()) for doc in docs],
        checklist_digest=checklist_digest(),
        needs_verification=provenance.needs_verification,
        verification_note=provenance.verification_note,
    )
