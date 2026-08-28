"""The profile contract the rule DSL is allowed to reference.

Rule expressions may only touch fields listed in `FIELDS`. Anything else is a load-time
error, so a typo in a YAML rule fails the build instead of silently evaluating to
UNKNOWN forever.

Field names mirror `citizen_profiles` columns in apps/api so the engine and the database
cannot drift.
"""

from __future__ import annotations

from typing import Literal

FieldKind = Literal["number", "string", "boolean"]


class Field:
    __slots__ = ("name", "kind", "choices", "question_i18n", "priority")

    def __init__(
        self,
        name: str,
        kind: FieldKind,
        question_i18n: dict[str, str],
        choices: tuple[str, ...] | None = None,
        priority: int = 100,
    ) -> None:
        self.name = name
        self.kind = kind
        self.choices = choices
        # Asked verbatim by the adaptive questionnaire (Phase 3/4).
        self.question_i18n = question_i18n
        # Lower sorts first when two fields would resolve equally many rules.
        self.priority = priority

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"Field({self.name!r}, {self.kind!r})"


SOCIAL_CATEGORIES = ("SC", "ST", "OBC", "GENERAL")

# Controlled vocabulary for project_sector. EDUCATION is what routes an applicant to the
# Educational Loan Scheme, so it is part of the contract, not a free-text value.
PROJECT_SECTORS = (
    "AGRICULTURE",
    "MANUFACTURING",
    "SERVICES",
    "TRADE",
    "TRANSPORT",
    "ARTISAN",
    "EDUCATION",
    "OTHER",
)

FIELDS: dict[str, Field] = {
    f.name: f
    for f in (
        Field(
            "category",
            "string",
            {
                "en": "Which social category do you belong to?",
                "hi": "आप किस सामाजिक श्रेणी से हैं?",
            },
            choices=SOCIAL_CATEGORIES,
            priority=10,
        ),
        Field(
            "project_sector",
            "string",
            {
                "en": "What do you need the money for?",
                "hi": "आपको पैसे की ज़रूरत किस लिए है?",
            },
            choices=PROJECT_SECTORS,
            priority=20,
        ),
        Field(
            "annual_family_income",
            "number",
            {
                "en": "What is your family's total yearly income?",
                "hi": "आपके परिवार की कुल वार्षिक आय कितनी है?",
            },
            priority=30,
        ),
        Field(
            "project_cost",
            "number",
            {
                "en": "How much money do you need in total?",
                "hi": "आपको कुल कितने पैसे की ज़रूरत है?",
            },
            priority=40,
        ),
        Field(
            "admission_confirmed",
            "boolean",
            {
                "en": "Has your admission been confirmed?",
                "hi": "क्या आपका प्रवेश पुष्ट हो चुका है?",
            },
            priority=50,
        ),
        Field(
            "age",
            "number",
            {"en": "How old are you?", "hi": "आपकी आयु कितनी है?"},
            priority=60,
        ),
        Field(
            "gender",
            "string",
            {"en": "What is your gender?", "hi": "आपका लिंग क्या है?"},
            choices=("FEMALE", "MALE", "OTHER", "UNDISCLOSED"),
            priority=70,
        ),
        Field(
            "has_caste_certificate",
            "boolean",
            {
                "en": "Do you have a caste certificate?",
                "hi": "क्या आपके पास जाति प्रमाण पत्र है?",
            },
            priority=80,
        ),
        Field(
            "existing_loans",
            "number",
            {
                "en": "How much do you still owe on other loans?",
                "hi": "अन्य ऋणों पर आप पर कितना बकाया है?",
            },
            priority=90,
        ),
        Field(
            "occupation_type",
            "string",
            {"en": "What work do you do?", "hi": "आप क्या काम करते हैं?"},
            priority=100,
        ),
        Field(
            "education_level",
            "string",
            {
                "en": "How far did you study?",
                "hi": "आपने कहाँ तक पढ़ाई की है?",
            },
            priority=110,
        ),
        Field(
            "sub_category",
            "string",
            {"en": "Any sub-category?", "hi": "कोई उप-श्रेणी?"},
            priority=120,
        ),
        Field(
            "is_pwd",
            "boolean",
            {
                "en": "Are you a person with disability?",
                "hi": "क्या आप दिव्यांग हैं?",
            },
            priority=130,
        ),
        Field(
            "is_safai_karamchari",
            "boolean",
            {
                "en": "Are you a Safai Karamchari or a dependent of one?",
                "hi": "क्या आप सफाई कर्मचारी हैं या उनके आश्रित हैं?",
            },
            priority=140,
        ),
    )
}

FIELD_NAMES = frozenset(FIELDS)


def validate_profile(profile: dict[str, object]) -> None:
    """Reject unknown keys and values outside a field's controlled vocabulary."""
    unknown = set(profile) - FIELD_NAMES
    if unknown:
        raise ValueError(f"Unknown profile field(s): {', '.join(sorted(unknown))}")

    for name, value in profile.items():
        if value is None:
            continue
        field = FIELDS[name]
        # bool is a subclass of int, so it must be excluded explicitly.
        if field.kind == "number" and (
            isinstance(value, bool) or not isinstance(value, int | float)
        ):
            raise ValueError(f"{name} must be a number, got {type(value).__name__}")
        if field.kind == "boolean" and not isinstance(value, bool):
            raise ValueError(f"{name} must be a boolean, got {type(value).__name__}")
        if field.kind == "string":
            if not isinstance(value, str):
                raise ValueError(f"{name} must be a string, got {type(value).__name__}")
            if field.choices and value not in field.choices:
                raise ValueError(
                    f"{name} must be one of {', '.join(field.choices)}, got {value!r}"
                )
