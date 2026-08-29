"""Turn messy human speech into a structured profile.

The division of labour is the point of this module:

  - A **deterministic** pass does the work that must be exactly right. Amounts go
    through `numerals.py`, categories and sectors through keyword tables. These carry
    high confidence and an evidence span pointing at the words they came from.
  - An **optional LLM** pass fills only the gaps the deterministic pass left, under a
    strict JSON schema, and never at high confidence.

The LLM cannot decide eligibility here and it cannot decide it downstream: everything
it produces is a candidate *fact* that the deterministic rule engine then judges. With
no API key configured the LLM pass is skipped entirely and the flow still completes,
which is both the offline story and the Phase 7 degradation story.

Anything below CONFIDENCE_THRESHOLD is not written to the profile. It becomes a
confirmation question, so a mis-heard income is corrected by the citizen rather than
silently deciding their eligibility.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.core.geography import DISTRICT_LOOKUP, STATE_LOOKUP
from app.services import llm
from app.services.numerals import normalise_digits, parse_amount

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.7

# The only fields extraction may ever produce. Anything else is a guardrail violation.
EXTRACTABLE_FIELDS: frozenset[str] = frozenset(
    {
        "annual_family_income",
        "project_cost",
        "project_sector",
        "occupation_type",
        "gender",
        "age",
        "education_level",
        "existing_loans",
        "is_pwd",
        "category",
        "admission_confirmed",
        "has_caste_certificate",
        "district",
        "state",
    }
)

# Fields that belong to the routing context rather than the eligibility profile.
CONTEXT_FIELDS: frozenset[str] = frozenset({"district", "state"})

PROFILE_FIELDS: frozenset[str] = EXTRACTABLE_FIELDS - CONTEXT_FIELDS


@dataclass(frozen=True, slots=True)
class ExtractedField:
    field: str
    value: Any
    confidence: float
    evidence_span: str
    source: str  # "deterministic" | "llm"

    def to_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "value": self.value,
            "confidence": round(self.confidence, 3),
            "evidence_span": self.evidence_span,
            "source": self.source,
        }


@dataclass(slots=True)
class ExtractionResult:
    accepted: list[ExtractedField] = field(default_factory=list)
    needs_confirmation: list[ExtractedField] = field(default_factory=list)
    rejected_fields: list[str] = field(default_factory=list)
    llm_used: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "accepted": [f.to_dict() for f in self.accepted],
            "needs_confirmation": [f.to_dict() for f in self.needs_confirmation],
            "rejected_fields": self.rejected_fields,
            "llm_used": self.llm_used,
        }


# --- keyword tables -----------------------------------------------------------------
# Romanised and native-script forms sit together: a citizen may type either.

INCOME_CUES = (
    "income", "salary", "earn", "earning", "annual", "yearly", "per year",
    "aay", "aamdani", "kamai", "salana", "saal ka", "varshik",
    "आय", "आमदनी", "कमाई", "सालाना", "वार्षिक", "वेतन",
)
COST_CUES = (
    "need", "want", "require", "requirement", "loan", "borrow", "cost", "budget",
    "chahiye", "zarurat", "jarurat", "karz", "rin",
    "चाहिए", "ज़रूरत", "जरूरत", "कर्ज", "ऋण", "लागत", "लोन",
)
EXISTING_LOAN_CUES = (
    "already have", "existing loan", "outstanding", "repaying", "baki", "bakaya",
    "पहले से", "बकाया", "चुका रहा", "पुराना कर्ज",
)

CATEGORY_CUES: dict[str, tuple[str, ...]] = {
    "SC": (
        "scheduled caste", "sc category", "anusuchit jati", "anusoochit jaati", "dalit",
        "अनुसूचित जाति", "दलित", "एससी",
    ),
    "ST": ("scheduled tribe", "st category", "adivasi", "अनुसूचित जनजाति", "आदिवासी"),
    "OBC": ("obc", "other backward", "pichhda varg", "अन्य पिछड़ा", "ओबीसी"),
    "GENERAL": ("general category", "samanya", "सामान्य वर्ग"),
}

SECTOR_CUES: dict[str, tuple[str, ...]] = {
    "EDUCATION": (
        "study", "studies", "college", "university", "degree", "course", "school",
        "bsc", "b.sc", "engineering course", "admission", "tuition", "fees",
        "padhai", "padhna", "shiksha", "vidyalaya",
        "पढ़ाई", "पढ़ना", "शिक्षा", "कॉलेज", "डिग्री", "प्रवेश", "फीस",
    ),
    "TRADE": (
        "shop", "vendor", "selling", "sell", "vegetable", "kirana", "stall", "cart",
        "retail", "trading", "dukan", "sabzi", "thela",
        "दुकान", "सब्जी", "ठेला", "बिक्री", "व्यापार",
    ),
    "MANUFACTURING": (
        "workshop", "factory", "manufactur", "furniture", "machine", "production",
        "karkhana", "nirman",
        "कारखाना", "फर्नीचर", "मशीन", "उत्पादन",
    ),
    "AGRICULTURE": (
        "farm", "farming", "crop", "dairy", "cattle", "poultry", "kheti", "krishi",
        "खेती", "कृषि", "डेयरी", "पशु",
    ),
    "TRANSPORT": (
        "auto", "rickshaw", "taxi", "tempo", "vehicle", "transport", "driver",
        "ऑटो", "रिक्शा", "टैक्सी", "वाहन", "परिवहन",
    ),
    "ARTISAN": (
        "handicraft", "weaving", "pottery", "tailor", "carpenter", "artisan",
        "bunkar", "darzi",
        "हस्तशिल्प", "बुनाई", "दर्जी", "बढ़ई", "कारीगर",
    ),
    "SERVICES": (
        "salon", "parlour", "parlor", "repair", "service centre", "tiffin", "catering",
        "सैलून", "पार्लर", "मरम्मत", "सेवा",
    ),
}

GENDER_CUES: dict[str, tuple[str, ...]] = {
    "FEMALE": ("woman", "female", "mahila", "aurat", "महिला", "औरत", "स्त्री"),
    "MALE": ("man", "male", "purush", "aadmi", "पुरुष", "आदमी"),
}

PWD_CUES = ("disabled", "disability", "divyang", "handicap", "दिव्यांग", "विकलांग")
CASTE_CERT_CUES = (
    "caste certificate", "jati praman", "जाति प्रमाण", "जाति प्रमाणपत्र",
)
ADMISSION_CUES = (
    "admission confirmed", "got admission", "admission mil", "seat confirmed",
    "प्रवेश मिल", "दाखिला मिल", "सीट मिल",
)
NEGATION_CUES = ("not", "no ", "nahi", "nahin", "नहीं", "ना ")

AGE_RE = re.compile(
    r"(\d{1,3})\s*(?:years?|yrs?|saal|sal|varsh|साल|वर्ष|बरस)", re.IGNORECASE
)


def _contains(haystack: str, needles: tuple[str, ...]) -> str | None:
    for needle in needles:
        if needle in haystack:
            return needle
    return None


def _negated_near(text: str, cue: str) -> bool:
    """Crude but useful: is there a negation within ~25 characters before the cue?"""
    index = text.find(cue)
    if index < 0:
        return False
    window = text[max(0, index - 25) : index + len(cue) + 12]
    return any(neg in window for neg in NEGATION_CUES)


def extract_deterministic(utterance: str, profile: dict[str, Any]) -> list[ExtractedField]:
    """Everything we can establish without a model."""
    text = normalise_digits(utterance).lower()
    found: list[ExtractedField] = []

    def add(name: str, value: Any, confidence: float, evidence: str) -> None:
        found.append(ExtractedField(name, value, confidence, evidence, "deterministic"))

    # --- amounts -------------------------------------------------------------------
    amount = parse_amount(utterance)
    if amount is not None:
        income_cue = _contains(text, INCOME_CUES)
        cost_cue = _contains(text, COST_CUES)
        loan_cue = _contains(text, EXISTING_LOAN_CUES)

        if loan_cue:
            add("existing_loans", amount.value, 0.90, amount.evidence)
        elif income_cue and not cost_cue:
            add("annual_family_income", amount.value, 0.95, amount.evidence)
        elif cost_cue and not income_cue:
            add("project_cost", amount.value, 0.95, amount.evidence)
        elif income_cue and cost_cue:
            # Both cues present and one amount: too ambiguous to write.
            add("annual_family_income", amount.value, 0.45, amount.evidence)
        else:
            # A bare number. We know the value exactly; we do not know what it is for.
            target = (
                "annual_family_income"
                if profile.get("annual_family_income") is None
                else "project_cost"
            )
            add(target, amount.value, 0.50, amount.evidence)

    # --- categorical fields --------------------------------------------------------
    for category, cues in CATEGORY_CUES.items():
        cue = _contains(text, cues)
        if cue:
            add("category", category, 0.95, cue)
            break

    for sector, cues in SECTOR_CUES.items():
        cue = _contains(text, cues)
        if cue:
            add("project_sector", sector, 0.88, cue)
            break

    for gender, cues in GENDER_CUES.items():
        cue = _contains(text, cues)
        if cue:
            add("gender", gender, 0.85, cue)
            break

    age_match = AGE_RE.search(text)
    if age_match:
        age = int(age_match.group(1))
        if 0 < age <= 120:
            add("age", age, 0.92, age_match.group(0))

    pwd_cue = _contains(text, PWD_CUES)
    if pwd_cue:
        add("is_pwd", not _negated_near(text, pwd_cue), 0.85, pwd_cue)

    cert_cue = _contains(text, CASTE_CERT_CUES)
    if cert_cue:
        add("has_caste_certificate", not _negated_near(text, cert_cue), 0.85, cert_cue)

    admission_cue = _contains(text, ADMISSION_CUES)
    if admission_cue:
        add("admission_confirmed", not _negated_near(text, admission_cue), 0.88, admission_cue)

    # --- place ---------------------------------------------------------------------
    for name, district in DISTRICT_LOOKUP.items():
        if name in text:
            add("district", district.name, 0.90, name)
            add("state", district.state, 0.85, name)
            break
    else:
        for name, state in STATE_LOOKUP.items():
            if name in text:
                add("state", state, 0.88, name)
                break

    return found


# --- optional LLM pass ---------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = """You extract factual fields from an applicant's own words \
for an Indian government credit scheme service.

You are a transcriber of facts, not a decision maker. You must never state, imply, or \
reason about whether the applicant qualifies for anything. A separate deterministic \
rule engine decides eligibility.

Rules:
- Return ONLY fields you have direct textual evidence for.
- Never guess. If the applicant did not say it, omit the field.
- evidence_span must be an exact substring of the applicant's message.
- confidence is your honest probability that the value is correct, 0.0 to 1.0.
- Do not convert or interpret monetary amounts; a separate parser handles those. Omit \
any money field.
- Output valid JSON only, with no commentary."""

EXTRACTION_TOOL = llm.ToolSpec(
    name="record_extracted_fields",
    description="Record fields explicitly stated by the applicant.",
    parameters={
        "type": "object",
        "properties": {
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {
                            "type": "string",
                            "enum": sorted(EXTRACTABLE_FIELDS - {"annual_family_income",
                                                                "project_cost",
                                                                "existing_loans"}),
                        },
                        "value": {},
                        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                        "evidence_span": {"type": "string"},
                    },
                    "required": ["field", "value", "confidence", "evidence_span"],
                },
            }
        },
        "required": ["fields"],
    },
)


def llm_available() -> bool:
    return llm.is_available()


async def extract_with_llm(
    utterance: str, language: str, missing: set[str]
) -> tuple[list[ExtractedField], list[str]]:
    """Fill only the gaps the deterministic pass left. Returns (fields, rejected)."""
    if not llm_available() or not missing:
        return [], []

    payload = await llm.complete_tool(
        system=EXTRACTION_SYSTEM_PROMPT,
        user=(
            f"Applicant message (language: {language}):\n{utterance}\n\n"
            f"Fields still unknown: {', '.join(sorted(missing))}"
        ),
        tool=EXTRACTION_TOOL,
    )
    if payload is None:
        # No model, a timeout, a bad model id — all the same to us: keep going with
        # what the deterministic pass found.
        return [], []

    return _validate_llm_fields(payload)


def _validate_llm_fields(payload: dict[str, Any]) -> tuple[list[ExtractedField], list[str]]:
    """Guardrail: anything outside the schema is dropped and logged, never trusted."""
    accepted: list[ExtractedField] = []
    rejected: list[str] = []

    for item in payload.get("fields", []):
        if not isinstance(item, dict):
            rejected.append(repr(item)[:60])
            continue
        name = item.get("field")
        if name not in EXTRACTABLE_FIELDS:
            logger.warning("guardrail: LLM returned out-of-schema field %r", name)
            rejected.append(str(name))
            continue
        try:
            confidence = float(item.get("confidence", 0.0))
        except (TypeError, ValueError):
            rejected.append(str(name))
            continue
        # The model never gets the benefit of the doubt on a money field.
        if name in {"annual_family_income", "project_cost", "existing_loans"}:
            logger.warning("guardrail: dropping LLM money field %r", name)
            rejected.append(str(name))
            continue
        value, ok = _coerce_to_contract(name, item.get("value"))
        if not ok:
            logger.warning(
                "guardrail: LLM value %r is outside the contract for %r", item.get("value"), name
            )
            rejected.append(str(name))
            continue

        accepted.append(
            ExtractedField(
                field=name,
                value=value,
                confidence=min(max(confidence, 0.0), 1.0),
                evidence_span=str(item.get("evidence_span", ""))[:200],
                source="llm",
            )
        )
    return accepted, rejected


def _coerce_to_contract(name: str, value: Any) -> tuple[Any, bool]:
    """Force a model-supplied value into the profile contract, or reject it.

    Models return semantically correct values in the wrong shape all the time —
    "female" for FEMALE, "sc" for SC, "25" for 25. Left alone these reach
    `validate_profile`, which raises, which surfaces to the citizen as a failed turn.
    A model quirk must never break a conversation, so normalise what is unambiguous and
    drop what is not.
    """
    from app.core.geography import DISTRICT_LOOKUP, STATE_LOOKUP

    if value is None:
        return None, False

    if name == "district":
        found = DISTRICT_LOOKUP.get(str(value).strip().casefold())
        return (found.name, True) if found else (None, False)
    if name == "state":
        found = STATE_LOOKUP.get(str(value).strip().casefold())
        return (found, True) if found else (None, False)

    from setu_rules import FIELDS

    field_spec = FIELDS.get(name)
    if field_spec is None:
        return None, False

    if field_spec.kind == "boolean":
        if isinstance(value, bool):
            return value, True
        text = str(value).strip().casefold()
        if text in {"true", "yes", "1"}:
            return True, True
        if text in {"false", "no", "0"}:
            return False, True
        return None, False

    if field_spec.kind == "number":
        if isinstance(value, bool):
            return None, False
        try:
            return float(value) if not isinstance(value, int) else value, True
        except (TypeError, ValueError):
            return None, False

    text = str(value).strip()
    if field_spec.choices:
        upper = text.upper().replace(" ", "_")
        return (upper, True) if upper in field_spec.choices else (None, False)
    return (text, True) if text else (None, False)


async def extract(
    utterance: str, language: str = "en", profile: dict[str, Any] | None = None
) -> ExtractionResult:
    """Extract facts from one utterance, splitting confident from uncertain."""
    profile = profile or {}
    result = ExtractionResult()

    candidates = extract_deterministic(utterance, profile)
    seen = {c.field for c in candidates}

    missing = {f for f in EXTRACTABLE_FIELDS if f not in seen and profile.get(f) is None}
    llm_fields, rejected = await extract_with_llm(utterance, language, missing)
    if llm_fields or rejected:
        result.llm_used = True
    result.rejected_fields = rejected

    # A deterministic reading always beats a model reading of the same field.
    for candidate in llm_fields:
        if candidate.field not in seen:
            candidates.append(candidate)
            seen.add(candidate.field)

    for candidate in candidates:
        if candidate.field not in EXTRACTABLE_FIELDS:
            result.rejected_fields.append(candidate.field)
            continue
        if candidate.confidence >= CONFIDENCE_THRESHOLD:
            result.accepted.append(candidate)
        else:
            result.needs_confirmation.append(candidate)

    return result


def confirmation_question(field_item: ExtractedField, language: str = "en") -> str:
    """Ask the citizen to confirm a low-confidence reading, in their words."""
    value = field_item.value
    if isinstance(value, int | float) and field_item.field in {
        "annual_family_income",
        "project_cost",
        "existing_loans",
    }:
        shown = f"Rs {value:,.0f}"
        hindi_shown = f"Rs {value:,.0f}"
    else:
        shown = hindi_shown = str(value)

    templates = {
        "annual_family_income": {
            "en": f"I heard your yearly family income is about {shown} — is that right?",
            "hi": f"मैंने समझा कि आपकी सालाना पारिवारिक आय लगभग {hindi_shown} है — क्या यह सही है?",
        },
        "project_cost": {
            "en": f"I heard you need about {shown} — is that right?",
            "hi": f"मैंने समझा कि आपको लगभग {hindi_shown} चाहिए — क्या यह सही है?",
        },
        "existing_loans": {
            "en": f"I heard you still owe about {shown} on other loans — is that right?",
            "hi": f"मैंने समझा कि आप पर अन्य ऋणों का लगभग {hindi_shown} बकाया है — क्या यह सही है?",
        },
    }
    default = {
        "en": f"I heard {field_item.field.replace('_', ' ')} is {shown} — is that right?",
        "hi": f"मैंने समझा कि {field_item.field.replace('_', ' ')} {shown} है — क्या यह सही है?",
    }
    entry = templates.get(field_item.field, default)
    return entry.get(language) or entry["en"]
