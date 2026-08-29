"""Indian numeral parsing. Deterministic, never delegated to a language model.

A citizen saying "ढाई लाख" and a citizen typing "2,50,000" mean the same Rs 250000, and
getting that wrong moves someone across the Rs 5,00,000 income ceiling. A model that is
right 98% of the time is wrong about one applicant in fifty, so this is a parser with
tests, not a prompt.

Handles:
  - Devanagari, Bengali, Tamil and Telugu digits alongside ASCII
  - Indian comma grouping: 2,50,000
  - Scale words in English, romanised Hindi and Devanagari: lakh/lac/लाख,
    crore/करोड़, thousand/hazaar/हज़ार, hundred/सौ
  - Compound amounts: "2 lakh 40 thousand"
  - Fraction words: ढाई 2.5, डेढ़ 1.5, आधा 0.5
  - Fraction modifiers on a following number: सवा +0.25, पौने -0.25, साढ़े +0.5
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# --- digit normalisation ------------------------------------------------------------

# Devanagari, Bengali, Tamil, Telugu digit blocks map onto 0-9.
_DIGIT_MAP = {
    **{chr(0x0966 + i): str(i) for i in range(10)},  # Devanagari
    **{chr(0x09E6 + i): str(i) for i in range(10)},  # Bengali
    **{chr(0x0BE6 + i): str(i) for i in range(10)},  # Tamil
    **{chr(0x0C66 + i): str(i) for i in range(10)},  # Telugu
}

SCALES: dict[str, int] = {
    "crore": 10_000_000,
    "crores": 10_000_000,
    "karod": 10_000_000,
    "karor": 10_000_000,
    "koti": 10_000_000,
    "करोड़": 10_000_000,
    "करोड": 10_000_000,
    "কোটি": 10_000_000,
    "கோடி": 10_000_000,
    "కోటి": 10_000_000,
    "lakh": 100_000,
    "lakhs": 100_000,
    "lac": 100_000,
    "lacs": 100_000,
    "lakhe": 100_000,
    "लाख": 100_000,
    "লাখ": 100_000,
    "লক্ষ": 100_000,
    "லட்சம்": 100_000,
    "లక్ష": 100_000,
    "thousand": 1_000,
    "thousands": 1_000,
    "hazaar": 1_000,
    "hazar": 1_000,
    "hajar": 1_000,
    "हज़ार": 1_000,
    "हजार": 1_000,
    "হাজার": 1_000,
    "ஆயிரம்": 1_000,
    "వేల": 1_000,
    "hundred": 100,
    "hundreds": 100,
    "sau": 100,
    "सौ": 100,
}

# Standalone quantity words.
WORD_NUMBERS: dict[str, float] = {
    "zero": 0, "shunya": 0, "शून्य": 0,
    "one": 1, "ek": 1, "एक": 1,
    "two": 2, "do": 2, "दो": 2,
    "three": 3, "teen": 3, "tin": 3, "तीन": 3,
    "four": 4, "char": 4, "chaar": 4, "चार": 4,
    "five": 5, "panch": 5, "paanch": 5, "पांच": 5, "पाँच": 5,
    "six": 6, "chah": 6, "cheh": 6, "छह": 6, "छे": 6,
    "seven": 7, "saat": 7, "सात": 7,
    "eight": 8, "aath": 8, "आठ": 8,
    "nine": 9, "nau": 9, "नौ": 9,
    "ten": 10, "das": 10, "दस": 10,
    "eleven": 11, "gyarah": 11, "ग्यारह": 11,
    "twelve": 12, "barah": 12, "बारह": 12,
    "fifteen": 15, "pandrah": 15, "पंद्रह": 15,
    "twenty": 20, "bees": 20, "बीस": 20,
    "twenty-five": 25, "pachees": 25, "पच्चीस": 25,
    "thirty": 30, "tees": 30, "तीस": 30,
    "forty": 40, "chalees": 40, "चालीस": 40,
    "fifty": 50, "pachas": 50, "पचास": 50,
    "sixty": 60, "saath": 60, "साठ": 60,
    "eighty": 80, "assi": 80, "अस्सी": 80,
    "hundred_word": 100,
    # Standalone fractions.
    "half": 0.5, "adha": 0.5, "aadha": 0.5, "आधा": 0.5,
    "dedh": 1.5, "derh": 1.5, "डेढ़": 1.5, "डेढ": 1.5,
    "dhai": 2.5, "adhai": 2.5, "ढाई": 2.5, "ढ़ाई": 2.5,
}

# Modifiers that adjust the number that follows them.
FRACTION_MODIFIERS: dict[str, float] = {
    "sava": 0.25, "sawa": 0.25, "सवा": 0.25,
    "paune": -0.25, "pone": -0.25, "पौने": -0.25,
    "sadhe": 0.5, "saadhe": 0.5, "साढ़े": 0.5, "साढे": 0.5,
}

_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass(frozen=True, slots=True)
class ParsedAmount:
    value: float
    evidence: str
    start: int
    end: int


def normalise_digits(text: str) -> str:
    """Map non-ASCII Indic digits to ASCII and strip Indian comma grouping."""
    out = "".join(_DIGIT_MAP.get(ch, ch) for ch in unicodedata.normalize("NFC", text))
    # 2,50,000 -> 250000. Only between digits, so "Nagpur, Maharashtra" is untouched.
    return re.sub(r"(?<=\d),(?=\d)", "", out)


def _tokenise(text: str) -> list[str]:
    lowered = normalise_digits(text).lower()
    # Keep Devanagari/Bengali/Tamil/Telugu letters, ASCII letters, digits and dots.
    return [t for t in re.split(r"[^\w.ऀ-෿]+", lowered) if t]


def _quantity(token: str) -> float | None:
    if _NUMBER_RE.fullmatch(token):
        return float(token)
    return WORD_NUMBERS.get(token)


def parse_amount(text: str) -> ParsedAmount | None:
    """Parse the first monetary amount in `text`, or None.

    Returns the value along with the substring it came from, so the caller can show a
    citizen exactly which words were read as a number.
    """
    tokens = _tokenise(text)
    if not tokens:
        return None

    total = 0.0
    pending: float | None = None
    modifier: float = 0.0
    matched = False
    used: list[str] = []

    for token in tokens:
        if token in FRACTION_MODIFIERS:
            modifier = FRACTION_MODIFIERS[token]
            used.append(token)
            continue

        if token in SCALES:
            scale = SCALES[token]
            base = pending if pending is not None else 1.0
            total += (base + modifier) * scale
            pending, modifier = None, 0.0
            matched = True
            used.append(token)
            continue

        quantity = _quantity(token)
        if quantity is not None:
            if pending is not None:
                # Two quantities with no scale between them: the earlier one stands
                # alone ("50 60 hazaar" is not a thing; take the later reading).
                total += pending + modifier
                modifier = 0.0
                matched = True
            pending = quantity
            used.append(token)
            continue

        # A non-numeric word ends the amount once we have read one.
        if matched or pending is not None:
            break

    if pending is not None:
        total += pending + modifier
        matched = True

    if not matched:
        return None

    evidence = _locate(text, used)
    return ParsedAmount(
        value=round(total, 2),
        evidence=evidence[0],
        start=evidence[1],
        end=evidence[2],
    )


def _locate(original: str, used: list[str]) -> tuple[str, int, int]:
    """Best-effort span of the tokens that produced the amount."""
    if not used:
        return "", 0, 0
    normalised = normalise_digits(original).lower()
    start = normalised.find(used[0])
    if start < 0:
        return " ".join(used), 0, 0
    end = start
    for token in used:
        found = normalised.find(token, end)
        if found >= 0:
            end = found + len(token)
    return original[start:end], start, end


def parse_rupees(text: str) -> float | None:
    """Convenience wrapper returning just the value."""
    parsed = parse_amount(text)
    return parsed.value if parsed else None
