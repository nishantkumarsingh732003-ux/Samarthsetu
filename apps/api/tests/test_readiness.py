"""Document readiness, as the partner console reports it.

The score exists so an officer can pick up the application that will actually move.
That makes two properties matter more than the arithmetic: it must name what is missing
(a bare percentage helps nobody), and it must never silently divide by zero on a scheme
family whose checklist is empty.
"""

from __future__ import annotations

from app.models import Application, Document, Scheme
from app.models.enums import DocumentValidationStatus, SchemeFamily
from app.services import readiness


def _scheme(family: SchemeFamily = SchemeFamily.MICRO_FINANCE) -> Scheme:
    scheme = Scheme()
    scheme.family = family
    scheme.code = "NSFDC_MICRO_FINANCE"
    scheme.official_name = "Micro Finance Scheme"
    return scheme


def _application(docs: list[Document] | None = None) -> Application:
    application = Application()
    application.documents = docs or []
    return application


def _document(
    doc_type: str,
    status: DocumentValidationStatus = DocumentValidationStatus.PASSED,
    redacted: bool = True,
) -> Document:
    doc = Document()
    doc.doc_type = doc_type
    doc.validation_status = status
    doc.redaction_applied = redacted
    return doc


def test_an_empty_application_scores_zero_and_names_everything() -> None:
    result = readiness.assess(_application(), _scheme())
    assert result.score == 0.0
    assert result.uploaded == 0
    assert result.required > 0
    assert len(result.missing) == result.required


def test_the_missing_list_is_human_readable_not_ids() -> None:
    """An officer reads this to a citizen down a phone. 'CASTE_CERTIFICATE' will not do."""
    result = readiness.assess(_application(), _scheme())
    assert all(" " in name or name.istitle() for name in result.missing)
    assert not any(name.isupper() and "_" in name for name in result.missing)


def test_uploading_a_required_document_raises_the_score() -> None:
    empty = readiness.assess(_application(), _scheme())
    one = readiness.assess(_application([_document("CASTE_CERTIFICATE")]), _scheme())
    assert one.score > empty.score
    assert one.uploaded == 1
    assert "Caste certificate" not in one.missing


def test_an_irrelevant_document_does_not_raise_the_score() -> None:
    """Uploading a fee structure to a micro-finance application is not progress."""
    empty = readiness.assess(_application(), _scheme())
    off_list = readiness.assess(_application([_document("FEE_STRUCTURE")]), _scheme())
    assert off_list.score == empty.score


def test_warnings_are_counted_separately_from_completeness() -> None:
    """A document that arrived but looks expired is present *and* a problem."""
    result = readiness.assess(
        _application(
            [_document("CASTE_CERTIFICATE", DocumentValidationStatus.WARNING)]
        ),
        _scheme(),
    )
    assert result.uploaded == 1
    assert result.warnings == 1


def test_an_id_document_stored_without_masking_is_surfaced() -> None:
    """OPEN_ITEMS OI-32: the officer is told to look at it themselves."""
    result = readiness.assess(
        _application([_document("IDENTITY_PROOF", redacted=False)]), _scheme()
    )
    assert result.unmasked_documents == 1


def test_a_masked_id_document_is_not_flagged() -> None:
    result = readiness.assess(
        _application([_document("IDENTITY_PROOF", redacted=True)]), _scheme()
    )
    assert result.unmasked_documents == 0


def test_a_student_application_asks_for_more_than_a_trader_one() -> None:
    trader = readiness.assess(_application(), _scheme(SchemeFamily.MICRO_FINANCE))
    student = readiness.assess(_application(), _scheme(SchemeFamily.EDUCATION_LOAN))
    assert student.required > trader.required


def test_the_score_is_bounded() -> None:
    docs = [
        _document(name)
        for name in (
            "CASTE_CERTIFICATE", "INCOME_CERTIFICATE", "IDENTITY_PROOF", "ADDRESS_PROOF",
            "BANK_PASSBOOK", "PHOTOGRAPH", "PROJECT_REPORT", "FEE_STRUCTURE",
        )
    ]
    result = readiness.assess(_application(docs), _scheme())
    assert 0.0 <= result.score <= 1.0
