"""Document upload, OCR pre-validation, and redaction.

Two jobs, in this order:

  1. **Redact before anything is stored.** A government ID is masked in the extracted
     text *and* painted over in the image itself. This happens before the file reaches
     disk, not as a cleanup pass afterwards.
  2. **Warn before submission, never block it.** Telling a citizen their income
     certificate looks two years old while they are still at home saves them a trip.
     Refusing their upload over it just moves the failure somewhere they cannot see.

OCR runs locally (tesseract). CLAUDE.md rule 4 and plain sense: an Aadhaar card does not
get uploaded to a third-party API to find out what it says.

**Failing closed.** If OCR is unavailable we cannot locate the ID region, so we cannot
paint over it. For a document type that carries a government ID, the upload is refused
rather than stored unredacted. Losing an upload is recoverable; leaking an Aadhaar
number is not.

**Where that guarantee stops.** A number OCR cannot read at all is a number we do not
know is there, so nothing is painted and the file is stored as it arrived. That case is
warned about (`NO_ID_DETECTED`) rather than refused, because refusing would block a
citizen whose only camera produces soft photos from supplying a required document. It is
tracked as OPEN_ITEMS OI-32 and is the reason redaction is not the only defence.
"""

from __future__ import annotations

import io
import logging
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Any

from app.models.enums import DocumentValidationStatus
from app.services import redaction

logger = logging.getLogger(__name__)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
ACCEPTED_TYPES = {"image/jpeg", "image/png", "image/webp", "application/pdf"}

# Documents whose upload is refused when redaction cannot run.
ID_BEARING_TYPES = {"IDENTITY_PROOF", "ADDRESS_PROOF"}


@dataclass(slots=True)
class Warning_:
    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(slots=True)
class AnalysisResult:
    doc_type: str
    detected_type: str | None
    validation_status: DocumentValidationStatus
    warnings: list[Warning_] = field(default_factory=list)
    extract: dict[str, Any] = field(default_factory=dict)
    masked_ids: list[dict[str, str]] = field(default_factory=list)
    redaction_applied: bool = False
    ocr_available: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "detected_type": self.detected_type,
            "validation_status": str(self.validation_status),
            "warnings": [w.to_dict() for w in self.warnings],
            "extract": self.extract,
            "masked_ids": self.masked_ids,
            "redaction_applied": self.redaction_applied,
            "ocr_available": self.ocr_available,
        }


class UnsupportedUpload(ValueError):
    """The file cannot be accepted at all."""


class RedactionUnavailable(RuntimeError):
    """An ID-bearing document arrived but redaction could not run."""


# --- OCR ------------------------------------------------------------------------------


def ocr_available() -> bool:
    try:
        import pytesseract  # noqa: PLC0415
        from PIL import Image  # noqa: F401,PLC0415

        pytesseract.get_tesseract_version()
        return True
    except Exception:  # noqa: BLE001 - any failure means we cannot OCR
        return False


def _load_image(data: bytes, content_type: str):
    """Return a PIL image for the first page, whatever was uploaded."""
    from PIL import Image  # noqa: PLC0415

    if content_type == "application/pdf":
        import fitz  # noqa: PLC0415  (PyMuPDF: self-contained, no poppler needed)

        with fitz.open(stream=data, filetype="pdf") as doc:
            if doc.page_count == 0:
                raise UnsupportedUpload("The PDF has no pages.")
            # 200 DPI: enough for OCR without making a 10MB scan unmanageable.
            pixmap = doc.load_page(0).get_pixmap(dpi=200)
            return Image.open(io.BytesIO(pixmap.tobytes("png"))).convert("RGB")

    return Image.open(io.BytesIO(data)).convert("RGB")


def _ocr_words(image) -> list[dict[str, Any]]:
    """Every recognised word with its bounding box."""
    import pytesseract  # noqa: PLC0415

    raw = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
    words = []
    for i, text in enumerate(raw["text"]):
        if not text.strip():
            continue
        words.append(
            {
                "text": text,
                "left": raw["left"][i],
                "top": raw["top"][i],
                "width": raw["width"][i],
                "height": raw["height"][i],
            }
        )
    return words


def redact_image(image, words: list[dict[str, Any]]):
    """Paint a filled rectangle over any word that looks like a government ID.

    Digits of an Aadhaar are often recognised as separate 4-digit words, so a run of
    adjacent numeric words on the same line is treated as one candidate. The box is
    padded outward: a redaction that clips the last digit is not a redaction.
    """
    from PIL import ImageDraw  # noqa: PLC0415

    draw = ImageDraw.Draw(image)
    painted = 0

    # Individual words that are themselves an ID.
    for word in words:
        if redaction.contains_government_id(word["text"]):
            _paint(draw, word)
            painted += 1

    # Runs of 4-digit groups on the same line: "1234 5678 9012".
    numeric = [w for w in words if re.fullmatch(r"\d{4}", w["text"])]
    numeric.sort(key=lambda w: (w["top"] // 12, w["left"]))
    for i in range(len(numeric) - 2):
        a, b, c = numeric[i], numeric[i + 1], numeric[i + 2]
        same_line = abs(a["top"] - b["top"]) < 12 and abs(b["top"] - c["top"]) < 12
        if same_line:
            for word in (a, b, c):
                _paint(draw, word)
            painted += 3

    return image, painted


def _paint(draw, word: dict[str, Any]) -> None:
    pad = 4
    draw.rectangle(
        [
            word["left"] - pad,
            word["top"] - pad,
            word["left"] + word["width"] + pad,
            word["top"] + word["height"] + pad,
        ],
        fill=(0, 0, 0),
    )


# --- classification and validation -----------------------------------------------------

TYPE_CUES: dict[str, tuple[str, ...]] = {
    "IDENTITY_PROOF": ("aadhaar", "आधार", "unique identification", "income tax department",
                       "permanent account number", "election commission", "elector"),
    "INCOME_CERTIFICATE": ("income certificate", "आय प्रमाण", "annual income", "tehsildar"),
    "CASTE_CERTIFICATE": ("caste certificate", "जाति प्रमाण", "scheduled caste",
                          "अनुसूचित जाति"),
    "BANK_PASSBOOK": ("passbook", "account number", "ifsc", "बैंक"),
    "ADMISSION_LETTER": ("admission", "provisional admission", "प्रवेश"),
    "FEE_STRUCTURE": ("fee structure", "tuition fee", "शुल्क"),
}

DATE_PATTERNS = (
    re.compile(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})"),
    re.compile(r"(\d{4})-(\d{2})-(\d{2})"),
)


def classify(text: str) -> str | None:
    lowered = text.lower()
    best: tuple[str, int] | None = None
    for doc_type, cues in TYPE_CUES.items():
        hits = sum(1 for cue in cues if cue in lowered)
        if hits and (best is None or hits > best[1]):
            best = (doc_type, hits)
    return best[0] if best else None


def extract_dates(text: str) -> list[date]:
    """Every plausible date, ignoring anything outside a sane range."""
    found: list[date] = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            groups = [int(g) for g in match.groups()]
            try:
                parsed = (
                    date(groups[0], groups[1], groups[2])
                    if groups[0] > 31
                    else date(groups[2], groups[1], groups[0])
                )
            except ValueError:
                continue
            if 1990 <= parsed.year <= date.today().year + 1:
                found.append(parsed)
    return sorted(found)


def validate(
    doc_type: str,
    detected_type: str | None,
    text: str,
    validity_months: int | None,
    today: date | None = None,
) -> list[Warning_]:
    """Warnings, never blocks. The citizen decides whether to proceed."""
    today = today or date.today()
    warnings: list[Warning_] = []

    if detected_type and detected_type != doc_type:
        warnings.append(
            Warning_(
                "TYPE_MISMATCH",
                f"This looks like a {detected_type.replace('_', ' ').lower()}, "
                f"but it was uploaded as {doc_type.replace('_', ' ').lower()}. "
                "Check you picked the right slot.",
            )
        )

    if not text.strip():
        warnings.append(
            Warning_(
                "NO_TEXT_FOUND",
                "We could not read any text. If the photo is blurred or dark, a clearer "
                "one will help the officer at the branch.",
            )
        )
        return warnings

    if validity_months:
        dates = extract_dates(text)
        if not dates:
            warnings.append(
                Warning_(
                    "NO_DATE_FOUND",
                    "We could not find an issue date. Most partners want this document "
                    f"issued within the last {validity_months} months.",
                )
            )
        else:
            newest = dates[-1]
            months_old = (today.year - newest.year) * 12 + (today.month - newest.month)
            if months_old > validity_months:
                warnings.append(
                    Warning_(
                        "POSSIBLY_EXPIRED",
                        f"This appears to be dated {newest.year}. Most partners require "
                        f"one issued within the last {validity_months} months.",
                    )
                )
    return warnings


# --- the entry point ---------------------------------------------------------------------


def analyse(
    data: bytes,
    content_type: str,
    doc_type: str,
    salt: str,
    validity_months: int | None = None,
    today: date | None = None,
) -> tuple[AnalysisResult, bytes]:
    """Analyse an upload and return the result plus the bytes that may be stored.

    The returned bytes are the redacted image when redaction ran, so a caller that
    writes what it is given cannot accidentally write the original.
    """
    if not data:
        raise UnsupportedUpload("The file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise UnsupportedUpload(
            f"The file is larger than {MAX_UPLOAD_BYTES // (1024 * 1024)}MB. "
            "Please take a smaller photo."
        )
    if content_type not in ACCEPTED_TYPES:
        raise UnsupportedUpload(f"{content_type} is not a supported file type.")

    result = AnalysisResult(
        doc_type=doc_type,
        detected_type=None,
        validation_status=DocumentValidationStatus.PENDING,
        ocr_available=ocr_available(),
    )

    if not result.ocr_available:
        # Cannot read it, therefore cannot find the ID region, therefore cannot mask it.
        if doc_type in ID_BEARING_TYPES:
            raise RedactionUnavailable(
                "This document usually carries a government ID and we cannot mask it "
                "right now, so we will not store it. Please try again shortly."
            )
        logger.warning("OCR unavailable; storing %s without pre-validation", doc_type)
        result.warnings.append(
            Warning_(
                "OCR_UNAVAILABLE",
                "We could not check this document automatically. The officer at the "
                "branch will review it.",
            )
        )
        return result, data

    image = _load_image(data, content_type)
    words = _ocr_words(image)
    text = " ".join(word["text"] for word in words)

    # --- redact FIRST, before anything else touches the bytes ---------------------------
    ids = redaction.find_government_ids(text, salt)
    redacted_image, painted = redact_image(image, words)
    result.masked_ids = [i.to_dict() for i in ids]
    result.redaction_applied = painted > 0

    if ids and painted == 0:
        # We found an ID in the text but could not locate it in the pixels. Storing the
        # image would leak it, so refuse.
        raise RedactionUnavailable(
            "We found an identity number on this document but could not mask it in the "
            "image, so we will not store it. Please upload a clearer photo."
        )

    redaction_warnings: list[Warning_] = []
    if doc_type in ID_BEARING_TYPES and not ids:
        # A document that is *supposed* to carry a number and appears not to. Either it
        # genuinely has none, or OCR could not read it — and we cannot tell which from
        # here, so nothing was painted and the image is stored as it arrived.
        #
        # This is the honest limit of automatic redaction (OPEN_ITEMS OI-32). We do not
        # refuse the upload, because that would block a citizen whose only camera
        # produces soft photos from ever supplying a required document. We say so
        # instead, to the citizen and in the audit trail.
        logger.warning("No government ID detected on a %s; stored without masking", doc_type)
        redaction_warnings.append(
            Warning_(
                "NO_ID_DETECTED",
                "We could not read an identity number on this photo, so nothing was "
                "blacked out. If the number is visible, please upload a clearer photo "
                "so we can mask it.",
            )
        )

    buffer = io.BytesIO()
    redacted_image.save(buffer, format="PNG", optimize=True)
    storable = buffer.getvalue()

    # --- everything below this line works on masked text only ---------------------------
    masked_text = redaction.mask_text(text)
    result.detected_type = classify(masked_text)
    result.extract = {
        "text_preview": masked_text[:400],
        "word_count": len(words),
        "dates_found": [d.isoformat() for d in extract_dates(masked_text)],
    }
    result.warnings = [
        *redaction_warnings,
        *validate(doc_type, result.detected_type, masked_text, validity_months, today),
    ]
    result.validation_status = (
        DocumentValidationStatus.WARNING if result.warnings else DocumentValidationStatus.PASSED
    )

    # Belt and braces before this ever reaches a caller that might persist it.
    redaction.assert_no_government_id(result.to_dict(), "document analysis")
    return result, storable
