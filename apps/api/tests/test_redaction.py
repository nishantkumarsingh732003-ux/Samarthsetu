"""Proof that a full Aadhaar number cannot be persisted.

CLAUDE.md rule 4 and the DPDP Act 2023: a government ID is masked at ingestion, and only
the last four digits plus a salted hash are retained.

This asserts that at every layer it could escape through:

  - the extracted **text** (mask_text)
  - the stored **image pixels** (redact_image)
  - the **analysis payload** that reaches the database (assert_no_government_id)
  - the **failure path**, where an unreadable ID document is refused rather than stored

The image test is the one that matters most, because it is the layer a reviewer cannot
verify by reading code: it renders a real Aadhaar-like card, runs the real pipeline, and
then OCRs the *output* to confirm the digits are gone from the pixels.
"""

from __future__ import annotations

import re

import pytest

from app.services import documents, redaction

SALT = "test-salt-not-a-real-one"

# Deliberately not a real Aadhaar (fails the Verhoeff checksum), but the right shape.
AADHAAR = "2345 6789 0123"
AADHAAR_DIGITS = "234567890123"


# --- layer 1: text ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "Aadhaar: 2345 6789 0123",
        "Aadhaar: 234567890123",
        "आधार 2345-6789-0123",
        "UID 2345 6789 0123 issued 01/01/2020",
        "23456789 0123",
    ],
)
def test_every_aadhaar_spelling_is_masked(text: str) -> None:
    masked = redaction.mask_text(text)
    assert AADHAAR_DIGITS not in re.sub(r"\D", "", masked)
    assert "0123" in masked, "the last four digits are kept on purpose"


def test_pan_and_voter_id_are_masked_too() -> None:
    assert "ABCDE1234F" not in redaction.mask_text("PAN ABCDE1234F")
    assert "ABC1234567" not in redaction.mask_text("EPIC ABC1234567")


def test_only_last4_and_a_salted_hash_are_retained() -> None:
    found = redaction.find_government_ids(f"Aadhaar {AADHAAR}", SALT)
    assert len(found) == 1
    record = found[0]
    assert record.id_type == "AADHAAR"
    assert record.last4 == "0123"
    assert AADHAAR_DIGITS not in record.salted_hash
    assert len(record.salted_hash) == 64


def test_the_hash_is_salted_so_it_cannot_be_reversed_by_rainbow_table() -> None:
    assert redaction.salted_hash(AADHAAR_DIGITS, "salt-a") != redaction.salted_hash(
        AADHAAR_DIGITS, "salt-b"
    )


def test_the_same_id_hashes_stably_under_one_salt() -> None:
    """Needed for de-duplication without ever holding the number."""
    assert redaction.salted_hash("2345 6789 0123", SALT) == redaction.salted_hash(
        "234567890123", SALT
    )


# --- layer 2: the persistence assertion --------------------------------------------------


def test_a_full_id_reaching_the_persistence_boundary_raises() -> None:
    """The last line of defence fails closed rather than writing."""
    with pytest.raises(redaction.UnmaskedGovernmentId):
        redaction.assert_no_government_id(
            {"ocr_extract": {"text": f"Aadhaar {AADHAAR}"}}, "document"
        )


def test_the_assertion_looks_inside_nested_structures() -> None:
    payload = {"a": [{"b": ("c", {"d": AADHAAR})}]}
    assert redaction.contains_government_id(payload)
    with pytest.raises(redaction.UnmaskedGovernmentId):
        redaction.assert_no_government_id(payload, "nested")


def test_masked_payloads_pass_the_assertion() -> None:
    masked = redaction.mask_text(f"Aadhaar {AADHAAR}")
    redaction.assert_no_government_id({"text": masked}, "masked")  # must not raise


# --- layer 3: the image pixels -----------------------------------------------------------


def _render_aadhaar_card():
    """A synthetic card carrying the number, large enough for OCR to read reliably."""
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (900, 320), "white")
    draw = ImageDraw.Draw(image)
    draw.text((40, 60), "Government of India", fill="black")
    draw.text((40, 110), "Name: Sunita Devi", fill="black")
    # Rendered large so tesseract reads the digits without a font dependency.
    for index, group in enumerate(AADHAAR.split()):
        draw.text((40 + index * 190, 190), group, fill="black")
    return image


def _ocr_digits(image) -> str:
    import pytesseract

    return re.sub(r"\D", "", pytesseract.image_to_string(image))


@pytest.mark.skipif(not documents.ocr_available(), reason="tesseract is not installed")
def test_the_stored_image_no_longer_contains_the_number() -> None:
    """THE test. Render a card, run the real pipeline, OCR the output.

    If the digits survive into the stored bytes, this fails — which is the only way to
    know redaction worked on pixels rather than merely on a string.
    """
    import io

    from PIL import Image

    card = _render_aadhaar_card()

    # Sanity: the number is genuinely readable before redaction, so a pass below means
    # redaction removed it rather than OCR never having seen it.
    assert AADHAAR_DIGITS in _ocr_digits(card), "OCR could not read the card at all"

    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    result, storable = documents.analyse(
        buffer.getvalue(),
        content_type="image/png",
        doc_type="IDENTITY_PROOF",
        salt=SALT,
    )

    assert result.redaction_applied
    assert [i["last4"] for i in result.masked_ids] == ["0123"]

    stored_image = Image.open(io.BytesIO(storable))
    assert AADHAAR_DIGITS not in _ocr_digits(stored_image), (
        "the Aadhaar number is still readable in the stored image"
    )


@pytest.mark.skipif(not documents.ocr_available(), reason="tesseract is not installed")
def test_the_analysis_payload_carries_no_full_id() -> None:
    """Whatever goes into ocr_extract must already be clean."""
    import io

    buffer = io.BytesIO()
    _render_aadhaar_card().save(buffer, format="PNG")
    result, _ = documents.analyse(
        buffer.getvalue(), "image/png", "IDENTITY_PROOF", SALT
    )
    redaction.assert_no_government_id(result.to_dict(), "analysis")  # must not raise
    assert AADHAAR_DIGITS not in str(result.to_dict())


# --- layer 4: the failure path -------------------------------------------------------------


def test_an_id_document_is_refused_when_ocr_is_unavailable(monkeypatch) -> None:
    """Fail closed: no OCR means no redaction, so the file is not stored at all."""
    monkeypatch.setattr(documents, "ocr_available", lambda: False)
    with pytest.raises(documents.RedactionUnavailable):
        documents.analyse(b"fake-bytes", "image/png", "IDENTITY_PROOF", SALT)


def test_a_non_id_document_still_uploads_when_ocr_is_unavailable(monkeypatch) -> None:
    """A project report carries no Aadhaar, so losing OCR must not lose the upload."""
    monkeypatch.setattr(documents, "ocr_available", lambda: False)
    result, storable = documents.analyse(b"fake-bytes", "image/png", "PROJECT_REPORT", SALT)
    assert storable == b"fake-bytes"
    assert [w.code for w in result.warnings] == ["OCR_UNAVAILABLE"]
    assert result.validation_status is documents.DocumentValidationStatus.PENDING


@pytest.mark.skipif(not documents.ocr_available(), reason="tesseract is not installed")
def test_an_id_found_in_text_but_not_locatable_in_pixels_is_refused(monkeypatch) -> None:
    """If we know an ID is there but cannot paint over it, storing would leak it."""
    import io

    monkeypatch.setattr(documents, "redact_image", lambda image, words: (image, 0))
    buffer = io.BytesIO()
    _render_aadhaar_card().save(buffer, format="PNG")
    with pytest.raises(documents.RedactionUnavailable):
        documents.analyse(buffer.getvalue(), "image/png", "IDENTITY_PROOF", SALT)


@pytest.mark.skipif(not documents.ocr_available(), reason="tesseract is not installed")
def test_an_id_document_with_no_readable_number_says_so(monkeypatch) -> None:
    """The honest limit of automatic redaction, made visible rather than silent.

    A blurred Aadhaar card yields no detected ID, so nothing is painted and the image is
    stored as it arrived. We do not refuse it — that would block a citizen whose only
    camera produces soft photos — but the citizen and the audit trail are both told.
    See OPEN_ITEMS OI-32.
    """
    import io

    from PIL import Image

    blank = Image.new("RGB", (600, 200), "white")
    buffer = io.BytesIO()
    blank.save(buffer, format="PNG")

    result, _ = documents.analyse(buffer.getvalue(), "image/png", "IDENTITY_PROOF", SALT)
    assert result.masked_ids == []
    assert result.redaction_applied is False
    assert "NO_ID_DETECTED" in [w.code for w in result.warnings]
