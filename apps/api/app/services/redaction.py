"""Government ID masking. The part of this system that must never fail open.

DPDP Act 2023 and CLAUDE.md rule 4: a government ID is masked at ingestion. Only the
last four digits and a salted hash are ever retained — of the text *and* of the image.

Three defences, deliberately layered, because any one of them can be defeated by a bug:

  1. `mask_text` rewrites every ID-shaped run in extracted text before it can be stored.
  2. `redact_image` paints a filled rectangle over the pixels OCR found the number in,
     so the stored file itself does not carry it.
  3. `assert_no_government_id` is a last-line assertion the persistence path calls. If a
     full number ever reaches it, it raises rather than writes.

The Aadhaar pattern is deliberately broad — any 12-digit run, spaced or not. A false
positive costs a masked phone number in an OCR extract nobody reads. A false negative
costs a citizen their Aadhaar number sitting in a database, which is not a trade this
project gets to make.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

# 12 digits, optionally grouped in 4s by spaces or hyphens. Verhoeff-valid Aadhaar is a
# subset of this; we mask the superset on purpose.
AADHAAR_RE = re.compile(r"(?<!\d)(\d{4})[\s-]?(\d{4})[\s-]?(\d{4})(?!\d)")

# PAN: five letters, four digits, one letter.
PAN_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{5})(\d{4})([A-Z])(?![A-Z0-9])")

# Voter EPIC: three letters then seven digits.
VOTER_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{3})(\d{7})(?![A-Z0-9])")

MASK_CHAR = "X"


@dataclass(frozen=True, slots=True)
class MaskedId:
    """What we are allowed to keep about a government ID."""

    id_type: str
    last4: str
    salted_hash: str

    def to_dict(self) -> dict[str, str]:
        return {"id_type": self.id_type, "last4": self.last4, "salted_hash": self.salted_hash}


def salted_hash(value: str, salt: str) -> str:
    """sha256(salt || digits). Lets us de-duplicate without holding the number."""
    digits = re.sub(r"\D", "", value)
    return hashlib.sha256(f"{salt}{digits}".encode()).hexdigest()


def mask_text(text: str) -> str:
    """Replace every government-ID-shaped run with a masked form keeping the last 4."""
    text = AADHAAR_RE.sub(lambda m: f"{MASK_CHAR * 4} {MASK_CHAR * 4} {m.group(3)}", text)
    text = PAN_RE.sub(lambda m: f"{MASK_CHAR * 5}{MASK_CHAR * 4}{m.group(3)}", text)
    text = VOTER_RE.sub(lambda m: f"{MASK_CHAR * 3}{MASK_CHAR * 3}{m.group(2)[-4:]}", text)
    return text


def find_government_ids(text: str, salt: str) -> list[MaskedId]:
    """Every ID in the text, reduced to what may be kept."""
    found: list[MaskedId] = []
    for match in AADHAAR_RE.finditer(text):
        digits = "".join(match.groups())
        found.append(MaskedId("AADHAAR", digits[-4:], salted_hash(digits, salt)))
    for match in PAN_RE.finditer(text):
        raw = match.group(0)
        found.append(MaskedId("PAN", raw[-4:], salted_hash(raw, salt)))
    for match in VOTER_RE.finditer(text):
        raw = match.group(0)
        found.append(MaskedId("VOTER_ID", raw[-4:], salted_hash(raw, salt)))
    return found


def contains_government_id(value: object) -> bool:
    """Does this value, anywhere inside it, still carry a full ID?"""
    if value is None:
        return False
    if isinstance(value, str):
        return bool(AADHAAR_RE.search(value) or PAN_RE.search(value) or VOTER_RE.search(value))
    if isinstance(value, dict):
        return any(contains_government_id(k) or contains_government_id(v) for k, v in value.items())
    if isinstance(value, list | tuple | set):
        return any(contains_government_id(item) for item in value)
    return contains_government_id(str(value)) if isinstance(value, int | float) else False


class UnmaskedGovernmentId(RuntimeError):
    """A full government ID reached the persistence boundary."""


def assert_no_government_id(payload: object, where: str) -> None:
    """Last line of defence, called before anything is written.

    Raising here loses one upload. Not raising here loses a citizen's Aadhaar number
    into a database, so this fails closed on purpose.
    """
    if contains_government_id(payload):
        raise UnmaskedGovernmentId(
            f"Refusing to persist {where}: it still contains a full government ID. "
            "Mask it with redaction.mask_text before storing."
        )
