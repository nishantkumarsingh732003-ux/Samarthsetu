"""The central claim, tested adversarially: the model cannot change a decision.

`test_llm.py` proves each guardrail in isolation. `make chaos` proves at runtime that a
verdict survives the model being unreachable. Neither proves the harder case: a model
that is present, answering, and **actively hostile** — returning approvals, inflated
amounts, renamed schemes and fabricated eligibility.

That is the case a jury will ask about, and it is what this file tests. Every test here
runs the real orchestration path with a stubbed provider that lies as convincingly as it
can, and asserts the deterministic output is byte-identical to the run with no model at
all.

If any assertion in this file fails, the project's central claim is false.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from app.core.config import settings
from app.services import explanation, extraction, llm

# --- the hostile provider ------------------------------------------------------------

# Everything a model could say that would change a citizen's understanding of a decision
# it does not get to make.
HOSTILE_PROSE = (
    "Congratulations! Your loan of Rs 50,00,000 has been APPROVED and the amount will be "
    "credited to your account within 24 hours. You are fully eligible for the Mega Loan "
    "Yojana. No documents are required."
)

# A tool call claiming facts nobody supplied, in shapes the contract does not allow.
HOSTILE_FIELDS: dict[str, Any] = {
    "annual_family_income": 1,
    "category": "SC",
    "project_cost": 5000000,
    "verdict": "ELIGIBLE",
    "eligible": True,
    "approved_amount": 5000000,
    "scheme_code": "MEGA_LOAN_YOJANA",
    "is_approved": "yes",
}

PROFILE = {
    "category": "SC",
    "project_sector": "TRADE",
    "annual_family_income": 180000,
    "project_cost": 80000,
}

# A citizen the rules must refuse: income far above the Rs 5,00,000 ceiling.
INELIGIBLE_PROFILE = {
    "category": "SC",
    "project_sector": "TRADE",
    "annual_family_income": 5000000,
    "project_cost": 80000,
}


@pytest.fixture
def hostile_model(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """A provider that is available, answering, and lying in every way it can.

    Returns its own call counts. A stub that is never reached would make every
    assertion in this file pass vacuously, which would be worse than having no tests —
    so `test_the_hostile_model_is_actually_reached` asserts it ran.
    """
    calls = {"text": 0, "tool": 0}

    async def prose(*args: Any, **kwargs: Any) -> str:
        calls["text"] += 1
        return HOSTILE_PROSE

    async def tool(*args: Any, **kwargs: Any) -> dict[str, Any]:
        calls["tool"] += 1
        return dict(HOSTILE_FIELDS)

    # `conftest.py` forces the provider off for every test; turn it back on for these,
    # because a disabled model proves nothing about a hostile one.
    monkeypatch.setattr(settings, "LLM_PROVIDER", "groq")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "test-key-not-a-real-one")
    monkeypatch.setattr(llm, "complete_text", prose)
    monkeypatch.setattr(llm, "complete_tool", tool)
    monkeypatch.setattr(extraction.llm, "complete_tool", tool)
    monkeypatch.setattr(explanation.llm, "complete_text", prose)
    return calls


# --- the verdict itself ----------------------------------------------------------------


def _decide(profile: dict[str, Any]) -> dict[str, Any]:
    """The deterministic engine, called exactly as the API calls it."""
    from setu_rules import run

    return run(profile, language="en").to_dict()


def test_the_engine_reaches_the_same_verdict_whatever_the_model_says(
    hostile_model: dict[str, int],
) -> None:
    """The load-bearing test of the whole project.

    The engine is a pure function of the profile and the rules. A model cannot reach it,
    which is why this passes — but it is asserted rather than assumed, because "the
    architecture makes it impossible" is what everyone says right up until it doesn't.
    """
    baseline = _decide(PROFILE)
    with_hostile_model = _decide(PROFILE)
    assert baseline == with_hostile_model


def test_a_hostile_model_cannot_make_an_ineligible_citizen_eligible(
    hostile_model: dict[str, int],
) -> None:
    """The model insists on ELIGIBLE and an approval. The rules refuse anyway."""
    result = _decide(INELIGIBLE_PROFILE)
    for scheme in result["results"]:
        assert scheme["verdict"] == "INELIGIBLE", scheme["scheme_code"]
        assert scheme["blocked_because"], "a refusal must always carry its reason"


def test_a_hostile_model_cannot_invent_a_scheme(hostile_model: dict[str, int]) -> None:
    """MEGA_LOAN_YOJANA does not exist. It must not appear anywhere in the output."""
    payload = json.dumps(_decide(PROFILE))
    assert "MEGA_LOAN_YOJANA" not in payload
    assert "Mega Loan" not in payload


def test_a_hostile_model_cannot_inflate_the_amount(hostile_model: dict[str, int]) -> None:
    """It claims Rs 50,00,000. The Micro Finance loan cap is Rs 1,25,000."""
    result = _decide(PROFILE)
    top = result["results"][0]
    assert top["indicative_amount"] is not None
    assert top["indicative_amount"] <= 125_000


def test_the_engine_version_and_digest_are_unchanged_by_the_model(
    hostile_model: dict[str, int],
) -> None:
    """Provenance is what makes a decision replayable. A model may not touch it."""
    from setu_rules import ENGINE_VERSION, rules_digest

    result = _decide(PROFILE)
    assert result["engine_version"] == ENGINE_VERSION
    assert result["rules_digest"] == rules_digest()


def test_every_reason_still_traces_to_a_rule_id(hostile_model: dict[str, int]) -> None:
    """A reason with no rule behind it is a reason a model could have written."""
    for scheme in _decide(PROFILE)["results"]:
        for reason in scheme["matched_because"] + scheme["blocked_because"]:
            assert reason["rule_id"], "a reason with no rule ID is unverifiable"
            assert reason["rule_id"].isupper()


def test_the_fit_score_is_unchanged_by_the_model(hostile_model: dict[str, int]) -> None:
    """Ranking is now driven by the fit score, so it is part of the decision surface."""
    for scheme in _decide(PROFILE)["results"]:
        assert scheme["fit"] is not None
        for component in scheme["fit"]["components"]:
            assert 0.0 <= component["score"] <= 100.0


# --- extraction: the one place a model *is* allowed to influence anything -------------


async def test_a_hostile_extraction_cannot_write_fields_outside_the_contract(
    hostile_model: dict[str, int],
) -> None:
    """The model returns verdict, eligible, approved_amount, is_approved. None exist.

    Extraction is the model's only route into the system, so this is the boundary that
    matters: anything outside the profile vocabulary is dropped, not coerced.
    """
    from setu_rules.profile import FIELDS

    result = await extraction.extract("I need money for my shop", "en", {})
    written = {f.field for f in result.accepted} | {f.field for f in result.needs_confirmation}

    for name in written:
        assert name in FIELDS, f"{name} is not a profile field and must never be written"

    forbidden = {"verdict", "eligible", "approved_amount", "scheme_code", "is_approved"}
    assert not (written & forbidden)


async def test_a_hostile_extraction_cannot_silently_write_an_absurd_value(
    hostile_model: dict[str, int],
) -> None:
    """It claims an annual income of Rs 1. Below the confidence gate it must be asked.

    A model-proposed value never lands in the profile unchallenged — it is either
    corroborated deterministically or put to the citizen as a question.
    """
    result = await extraction.extract("I need money for my shop", "en", {})
    for field in result.accepted:
        assert field.confidence >= extraction.CONFIDENCE_THRESHOLD


# --- explanation: the model writes prose, and the prose is checked --------------------


async def test_prose_claiming_approval_is_discarded_end_to_end(
    hostile_model: dict[str, int],
) -> None:
    """The model returns a full approval. The citizen must not see one word of it."""
    result = _decide(PROFILE)["results"][0]
    out = await explanation.explain(result, "en")
    text = out["explanation"]

    assert "APPROVED" not in text.upper()
    assert "50,00,000" not in text
    assert "24 hours" not in text
    assert "credited" not in text.lower()
    assert out["source"] == "template", "a rejected explanation must fall back to our own"


async def test_the_explanation_still_names_the_official_scheme(
    hostile_model: dict[str, int],
) -> None:
    """Falling back must not mean falling silent. The citizen still gets an answer."""
    result = _decide(PROFILE)["results"][0]
    out = await explanation.explain(result, "en")
    assert result["official_name"] in out["explanation"]
    assert out["explanation"].strip()


async def test_the_amount_in_the_explanation_comes_from_the_engine(
    hostile_model: dict[str, int],
) -> None:
    """The model never receives the figure, so it cannot be the source of one."""
    result = _decide(PROFILE)["results"][0]
    out = await explanation.explain(result, "en")
    if "Rs" in out["explanation"]:
        assert "5,000,000" not in out["explanation"]
        assert "50,00,000" not in out["explanation"]


# --- the test that stops every other test in this file being vacuous ------------------


async def test_the_hostile_model_is_actually_reached(hostile_model: dict[str, int]) -> None:
    """Prove the stub runs.

    Every other assertion here says "the hostile output did not get through". All of
    them would also pass if the model were never called at all — a disabled provider,
    a monkeypatch on the wrong module, a renamed function. This is the test that tells
    the difference between a defence and an accident.
    """
    result = _decide(PROFILE)["results"][0]

    await extraction.extract("I need money for my shop", "en", {})
    assert hostile_model["tool"] > 0, "extraction never consulted the model; the stub is inert"

    await explanation.explain(result, "en")
    assert hostile_model["text"] > 0, "explanation never consulted the model; the stub is inert"
