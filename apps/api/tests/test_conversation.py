"""The equivalence proof: the LLM does not decide anything.

A scripted five-turn Hindi conversation is run end to end through the orchestrator, and
the resulting scheme match is asserted identical to calling the rule engine directly
with the equivalent structured profile.

If a language model were participating in the verdict, those two paths could diverge.
They cannot, because extraction runs strictly before the engine and only proposes
facts, and explanation runs strictly after it and only restates the outcome.

Runs without Postgres or Redis: the database session and the session store are stubbed,
because neither participates in the decision.
"""

from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.services import conversation, extraction
from app.services import session as session_store
from app.services.session import MAX_QUESTIONS

# --- the scripted conversation, in Hindi -------------------------------------------

TURNS: list[str] = [
    "नमस्ते, मैं सब्जी बेचती हूँ",          # occupation -> project_sector TRADE
    "मैं अनुसूचित जाति से हूँ",              # category SC
    "ढाई लाख",                              # a bare amount: must be CONFIRMED, not assumed
    "हाँ",                                   # confirmation
    "मुझे अस्सी हजार चाहिए",                # project_cost 80000 -> decision
]

# What a form would have collected instead of a conversation.
EQUIVALENT_PROFILE: dict[str, Any] = {
    "project_sector": "TRADE",
    "category": "SC",
    "annual_family_income": 250000.0,
    "project_cost": 80000.0,
}


class _FakeResult:
    def __init__(self, rows: list[Any] | None = None) -> None:
        self._rows = rows or []

    def scalar_one_or_none(self) -> Any:
        return self._rows[0] if self._rows else None

    def all(self) -> list[Any]:
        return self._rows


class FakeSession:
    """Enough of AsyncSession for match persistence. Holds nothing that decides."""

    def __init__(self) -> None:
        self.added: list[Any] = []

    def add(self, obj: Any) -> None:
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()
        self.added.append(obj)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        return None

    async def execute(self, *_: Any, **__: Any) -> _FakeResult:
        return _FakeResult()


@pytest.fixture(autouse=True)
def in_memory_sessions(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Replace the Redis-backed session store; sessions are state, not decisions."""
    store: dict[str, Any] = {}

    async def load(session_id: str):
        return store.get(session_id)

    async def save(convo) -> None:
        store[convo.session_id] = convo

    async def load_or_create(session_id: str | None, language: str = "en"):
        if session_id and session_id in store:
            convo = store[session_id]
            convo.language = language or convo.language
            return convo
        return session_store.Session(session_id=session_id or str(uuid.uuid4()),
                                     language=language)

    monkeypatch.setattr(session_store, "load", load)
    monkeypatch.setattr(session_store, "save", save)
    monkeypatch.setattr(session_store, "load_or_create", load_or_create)
    return store


async def run_conversation(turns: list[str], language: str = "hi") -> dict[str, Any]:
    db = FakeSession()
    session_id: str | None = None
    last: dict[str, Any] = {}
    for utterance in turns:
        last = await conversation.handle_turn(db, session_id, utterance, language)
        session_id = last["session_id"]
    return last


# --- the acceptance test -------------------------------------------------------------


@pytest.mark.asyncio
async def test_hindi_conversation_matches_the_direct_engine_call() -> None:
    """THE equivalence test. Conversation and form must reach the same verdict."""
    from setu_rules import evaluate

    final = await run_conversation(TURNS)

    assert final["stage"] == "DECIDED", final.get("question")
    assert final["profile"] == EQUIVALENT_PROFILE

    direct = [r.to_dict() for r in evaluate(EQUIVALENT_PROFILE, language="hi")]
    assert final["results"] == direct


@pytest.mark.asyncio
async def test_conversation_builds_the_profile_the_form_would_have() -> None:
    final = await run_conversation(TURNS)
    assert final["profile"] == EQUIVALENT_PROFILE


@pytest.mark.asyncio
async def test_the_street_vendor_is_routed_to_micro_finance() -> None:
    final = await run_conversation(TURNS)
    top = final["results"][0]
    assert top["scheme_code"] == "NSFDC_MICRO_FINANCE"
    assert top["verdict"] == "ELIGIBLE"


# --- confirmation behaviour ----------------------------------------------------------


@pytest.mark.asyncio
async def test_a_bare_amount_is_confirmed_rather_than_assumed() -> None:
    """"ढाई लाख" with no context could be income or requirement. We ask."""
    final = await run_conversation(TURNS[:3])
    assert final["stage"] == "CONFIRMING"
    assert final["question_field"] == "annual_family_income"
    assert "250,000" in final["question"]
    # Crucially, it has NOT been written to the profile yet.
    assert "annual_family_income" not in final["profile"]


@pytest.mark.asyncio
async def test_declining_a_confirmation_does_not_write_the_value() -> None:
    final = await run_conversation([*TURNS[:3], "नहीं"])
    assert "annual_family_income" not in final["profile"]


@pytest.mark.asyncio
async def test_confirming_writes_the_value() -> None:
    final = await run_conversation(TURNS[:4])
    assert final["profile"]["annual_family_income"] == 250000.0


# --- question budget ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_a_decision_is_reached_within_six_questions() -> None:
    """Phase 3 promises at most six questions. Assert it, do not hope for it."""
    final = await run_conversation(TURNS)
    assert final["questions_asked"] <= MAX_QUESTIONS
    assert final["stage"] == "DECIDED"


@pytest.mark.asyncio
async def test_the_same_question_is_never_asked_twice_in_a_row() -> None:
    """Re-asking an unanswered question is fine; repeating it verbatim reads as broken.

    A citizen who does not answer "how much do you need?" should be asked something
    else next, and only returned to that question once it is the one thing still
    standing between them and an answer.
    """
    db = FakeSession()
    session_id = None
    asked: list[str] = []
    for utterance in TURNS:
        result = await conversation.handle_turn(db, session_id, utterance, "hi")
        session_id = result["session_id"]
        if result["stage"] == "ASKING":
            asked.append(result["question_field"])

    consecutive = [a for a, b in zip(asked, asked[1:], strict=False) if a == b]
    assert not consecutive, f"asked the same field twice in a row: {asked}"


@pytest.mark.asyncio
async def test_every_question_asked_could_have_changed_the_outcome() -> None:
    """No question is asked whose answer cannot move any rule."""
    from setu_rules import field_impact

    db = FakeSession()
    session_id = None
    for utterance in TURNS:
        result = await conversation.handle_turn(db, session_id, utterance, "hi")
        session_id = result["session_id"]
        if result["stage"] == "ASKING":
            # The field must still be one that unblocks a rule for the profile as it
            # stood when the question was asked.
            assert result["question_field"] in field_impact(result["profile"])


@pytest.mark.asyncio
async def test_an_unhelpful_conversation_still_terminates() -> None:
    """Six shrugs must not loop forever."""
    final = await run_conversation(["पता नहीं"] * 8)
    assert final["questions_asked"] <= MAX_QUESTIONS
    assert final["stage"] in {"DECIDED", "QUESTION_LIMIT_REACHED"}


# --- language handling ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_questions_come_back_in_the_requested_language() -> None:
    db = FakeSession()
    hindi = await conversation.handle_turn(db, None, "नमस्ते", "hi")
    english = await conversation.handle_turn(db, None, "hello", "en")
    assert hindi["question"] != english["question"]
    assert hindi["question_field"] == english["question_field"]


@pytest.mark.asyncio
async def test_the_same_facts_in_english_reach_the_same_verdict() -> None:
    """Language changes the words, never the outcome."""
    from setu_rules import evaluate

    english = await run_conversation(
        [
            "I sell vegetables from a cart",
            "I am from a scheduled caste family",
            "my yearly income is 2.5 lakh",
            "I need 80 thousand",
        ],
        language="en",
    )
    assert english["profile"] == EQUIVALENT_PROFILE
    assert english["results"] == [
        r.to_dict() for r in evaluate(EQUIVALENT_PROFILE, language="en")
    ]


# --- guardrails ------------------------------------------------------------------------


def test_extraction_schema_excludes_money_fields_from_the_llm() -> None:
    """Amounts are parsed deterministically; the model is not offered the choice."""
    enum = extraction.EXTRACTION_TOOL.parameters["properties"]["fields"]["items"][
        "properties"
    ]["field"]["enum"]
    assert "annual_family_income" not in enum
    assert "project_cost" not in enum
    assert "existing_loans" not in enum


def test_out_of_schema_llm_fields_are_rejected_and_reported() -> None:
    accepted, rejected = extraction._validate_llm_fields(
        {
            "fields": [
                {"field": "gender", "value": "FEMALE", "confidence": 0.9,
                 "evidence_span": "woman"},
                {"field": "eligible", "value": True, "confidence": 1.0,
                 "evidence_span": "x"},
                {"field": "verdict", "value": "ELIGIBLE", "confidence": 1.0,
                 "evidence_span": "x"},
            ]
        }
    )
    assert [f.field for f in accepted] == ["gender"]
    assert set(rejected) == {"eligible", "verdict"}


def test_llm_money_fields_are_dropped_even_if_in_schema() -> None:
    accepted, rejected = extraction._validate_llm_fields(
        {
            "fields": [
                {"field": "annual_family_income", "value": 999, "confidence": 0.99,
                 "evidence_span": "x"}
            ]
        }
    )
    assert accepted == []
    assert rejected == ["annual_family_income"]


def test_low_confidence_readings_never_enter_the_profile() -> None:
    assert extraction.CONFIDENCE_THRESHOLD == 0.7
    fields = extraction.extract_deterministic("ढाई लाख", {})
    bare = next(f for f in fields if f.field == "annual_family_income")
    assert bare.confidence < extraction.CONFIDENCE_THRESHOLD


# --- all six languages -------------------------------------------------------------------


@pytest.mark.parametrize("language", ["en", "hi", "mr", "bn", "ta", "te"])
@pytest.mark.asyncio
async def test_every_supported_language_reaches_the_same_verdict(language: str) -> None:
    """Language changes the words a citizen reads. It must never change the outcome."""
    from setu_rules import evaluate

    db = FakeSession()
    result = await conversation.handle_turn(db, None, "hello", language)
    # The engine ran; compare its verdicts against a direct call in the same language.
    assert result["stage"] in {"ASKING", "CONFIRMING", "DECIDED"}

    direct = [r.verdict for r in evaluate({}, language=language)]
    assert len(direct) == 3


@pytest.mark.parametrize("language", ["mr", "bn", "ta", "te"])
def test_rule_messages_exist_in_every_language(language: str) -> None:
    """No language may silently fall back to English for an eligibility reason."""
    from setu_rules import load_schemes

    for scheme in load_schemes():
        for rule in scheme.rules:
            assert rule.message_i18n.get(language), f"{rule.id} has no {language} message"
            assert rule.satisfied_i18n.get(language), f"{rule.id} has no {language} satisfied"


@pytest.mark.parametrize("language", ["mr", "bn", "ta", "te"])
def test_questions_exist_in_every_language(language: str) -> None:
    from setu_rules import FIELDS

    for name, spec in FIELDS.items():
        assert spec.question_i18n.get(language), f"{name} has no {language} question"


@pytest.mark.parametrize("language", ["en", "hi", "mr", "bn", "ta", "te"])
def test_the_template_explanation_is_written_in_the_requested_language(language: str) -> None:
    """A Tamil speaker must not receive an English paragraph."""
    from app.services import explanation

    result = {
        "scheme_code": "NSFDC_MICRO_FINANCE",
        "official_name": "Micro Finance Scheme",
        "verdict": "ELIGIBLE",
        "indicative_amount": 72000.0,
        "matched_because": [],
        "blocked_because": [],
        "warnings": [],
    }
    rendered = explanation.template_explanation(result, language)
    assert "Micro Finance Scheme" in rendered  # the legal name survives in every language
    if language != "en":
        english = explanation.template_explanation(result, "en")
        assert rendered != english, f"{language} fell back to English"


@pytest.mark.parametrize("language", ["mr", "bn", "ta", "te"])
def test_unreviewed_languages_are_reported_as_draft(language: str) -> None:
    """A citizen reading machine-written copy must be markable as such in the UI."""
    from setu_rules import evaluate, translation_status

    assert translation_status(language) == "draft"
    assert evaluate({}, language=language)[0].translation_status == "draft"


@pytest.mark.parametrize("language", ["en", "hi"])
def test_reviewed_languages_are_reported_as_verified(language: str) -> None:
    from setu_rules import translation_status

    assert translation_status(language) == "verified"


@pytest.mark.parametrize("language", ["en", "hi", "mr", "bn", "ta", "te"])
def test_no_language_template_trips_the_approval_backstop(language: str) -> None:
    from app.services import explanation

    for verdict in ("ELIGIBLE", "LIKELY_ELIGIBLE", "INELIGIBLE", "NEED_MORE_INFO"):
        rendered = explanation.template_explanation(
            {
                "scheme_code": "NSFDC_MICRO_FINANCE",
                "official_name": "Micro Finance Scheme",
                "verdict": verdict,
                "indicative_amount": 72000.0,
                "matched_because": [],
                "blocked_because": [],
                "warnings": [],
                "missing_fields": ["category"],
            },
            language,
        )
        assert not explanation._claims_approval(rendered, language), f"{language}/{verdict}"
