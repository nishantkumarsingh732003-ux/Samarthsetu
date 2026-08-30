"""How close an application is to being processable.

The partner console's job is to let an officer pick up the application that will move
fastest, and to tell a citizen precisely what is holding theirs up. A single "80%" would
do neither. So the score comes with the list of documents actually missing, and the
count of documents that uploaded but raised a warning.

The score is a ratio of documents supplied to documents required — deliberately not a
weighted model. A weighted score would encode a judgement about which document matters
most, and that judgement belongs to the Channel Partner, not to us.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.models import Application, Scheme
from app.models.enums import DocumentValidationStatus


@dataclass(slots=True)
class Readiness:
    score: float
    uploaded: int
    required: int
    missing: list[str] = field(default_factory=list)
    warnings: int = 0
    unmasked_documents: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "uploaded": self.uploaded,
            "required": self.required,
            "missing": self.missing,
            "warnings": self.warnings,
            "unmasked_documents": self.unmasked_documents,
        }


def assess(
    application: Application,
    scheme: Scheme,
    partner_type: str | None = None,
    language: str = "en",
) -> Readiness:
    """Score one application against the checklist its scheme family requires."""
    from setu_rules.documents import required_documents

    required = required_documents(
        family=str(scheme.family), partner_type=partner_type, profile={}, language=language
    )
    required_ids = [doc.id for doc in required]
    by_name = {doc.id: doc.name for doc in required}

    uploaded_types = {doc.doc_type for doc in application.documents}
    present = [doc_id for doc_id in required_ids if doc_id in uploaded_types]

    warnings = sum(
        1
        for doc in application.documents
        if doc.validation_status is DocumentValidationStatus.WARNING
    )
    # A document that carries an ID but was stored without one being masked. Surfaced to
    # the officer because they should look at it themselves (OPEN_ITEMS OI-32).
    unmasked = sum(
        1
        for doc in application.documents
        if doc.doc_type in {"IDENTITY_PROOF", "ADDRESS_PROOF"} and not doc.redaction_applied
    )

    return Readiness(
        # An application for a scheme with no checklist is ready, not divided by zero.
        score=round(len(present) / len(required_ids), 3) if required_ids else 1.0,
        uploaded=len(present),
        required=len(required_ids),
        missing=[by_name[doc_id] for doc_id in required_ids if doc_id not in uploaded_types],
        warnings=warnings,
        unmasked_documents=unmasked,
    )
