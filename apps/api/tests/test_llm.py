"""Provider resolution and the guarantee that a model is never load-bearing.

The rule engine does not call a model, so no test here asserts anything about a
verdict. What is asserted is that every way a provider can be absent, misconfigured or
broken produces a clean fallback rather than an error reaching the citizen.
"""

from __future__ import annotations

import pytest

from app.core.config import settings
from app.services import explanation, extraction, llm


@pytest.fixture
def env(monkeypatch: pytest.MonkeyPatch):
    """Set provider settings for one test."""

    def _set(provider: str = "auto", anthropic: str = "", xai: str = "",
             groq: str = "", model: str = ""):
        monkeypatch.setattr(settings, "LLM_PROVIDER", provider)
        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", anthropic)
        monkeypatch.setattr(settings, "XAI_API_KEY", xai)
        monkeypatch.setattr(settings, "GROQ_API_KEY", groq)
        monkeypatch.setattr(settings, "LLM_MODEL", model)

    return _set


# --- provider resolution --------------------------------------------------------------


def test_no_keys_resolves_to_none(env) -> None:
    env()
    assert llm.resolve_provider() is llm.Provider.NONE
    assert not llm.is_available()


def test_auto_picks_the_provider_whose_key_is_set(env) -> None:
    env(xai="xai-key")
    assert llm.resolve_provider() is llm.Provider.XAI

    env(anthropic="ant-key")
    assert llm.resolve_provider() is llm.Provider.ANTHROPIC


def test_auto_prefers_xai_when_both_keys_are_present(env) -> None:
    env(anthropic="ant-key", xai="xai-key")
    assert llm.resolve_provider() is llm.Provider.XAI


def test_groq_is_recognised_and_distinct_from_xai(env) -> None:
    """Groq (gsk_ keys, open models) is not xAI (Grok). Confusing them is the whole
    reason both are named explicitly."""
    env(groq="gsk-key")
    assert llm.resolve_provider() is llm.Provider.GROQ
    assert llm.resolve_model() == llm.DEFAULT_MODELS[llm.Provider.GROQ]
    assert "groq.com" in settings.GROQ_BASE_URL


def test_asking_for_xai_with_only_a_groq_key_is_none(env) -> None:
    """A Groq key must never be silently used as if it were an xAI key."""
    env(provider="xai", groq="gsk-key")
    assert llm.resolve_provider() is llm.Provider.NONE


def test_groq_and_xai_share_the_openai_wire_format(env) -> None:
    assert llm.Provider.GROQ in llm.OPENAI_COMPATIBLE
    assert llm.Provider.XAI in llm.OPENAI_COMPATIBLE
    assert llm.Provider.ANTHROPIC not in llm.OPENAI_COMPATIBLE


def test_explicit_provider_overrides_auto_detection(env) -> None:
    env(provider="anthropic", anthropic="ant-key", xai="xai-key")
    assert llm.resolve_provider() is llm.Provider.ANTHROPIC


def test_explicit_provider_without_its_key_is_none_not_a_silent_fallback(env) -> None:
    """Asking for xai with no xai key must not quietly use Anthropic instead."""
    env(provider="xai", anthropic="ant-key")
    assert llm.resolve_provider() is llm.Provider.NONE


def test_none_disables_the_model_even_when_a_key_exists(env) -> None:
    env(provider="none", xai="xai-key", anthropic="ant-key")
    assert llm.resolve_provider() is llm.Provider.NONE
    assert not llm.is_available()


def test_blank_model_falls_back_to_the_provider_default(env) -> None:
    env(xai="xai-key")
    assert llm.resolve_model() == llm.DEFAULT_MODELS[llm.Provider.XAI]
    env(anthropic="ant-key")
    assert llm.resolve_model() == llm.DEFAULT_MODELS[llm.Provider.ANTHROPIC]


def test_explicit_model_wins(env) -> None:
    env(xai="xai-key", model="grok-custom")
    assert llm.resolve_model() == "grok-custom"


def test_describe_never_leaks_a_key(env) -> None:
    env(xai="xai-super-secret-key", anthropic="ant-super-secret-key",
        groq="gsk-super-secret-key")
    rendered = repr(llm.describe())
    assert "super-secret" not in rendered
    assert llm.describe()["xai_key_present"] is True


# --- tool schema is provider-neutral ---------------------------------------------------


def test_tool_spec_renders_for_both_providers() -> None:
    spec = llm.ToolSpec(name="t", description="d", parameters={"type": "object"})
    assert spec.as_anthropic()["input_schema"] == {"type": "object"}
    assert spec.as_openai()["function"]["parameters"] == {"type": "object"}
    assert spec.as_openai()["type"] == "function"


def test_the_extraction_tool_offers_no_money_field_to_any_provider() -> None:
    """Amounts are parsed deterministically regardless of which vendor is wired up."""
    enum = extraction.EXTRACTION_TOOL.parameters["properties"]["fields"]["items"][
        "properties"
    ]["field"]["enum"]
    assert not {"annual_family_income", "project_cost", "existing_loans"} & set(enum)


# --- failure is always a fallback, never an error ---------------------------------------


@pytest.mark.asyncio
async def test_text_completion_returns_none_when_disabled(env) -> None:
    env(provider="none")
    assert await llm.complete_text("s", "u") is None


@pytest.mark.asyncio
async def test_tool_completion_returns_none_when_disabled(env) -> None:
    env(provider="none")
    spec = llm.ToolSpec(name="t", description="d", parameters={"type": "object"})
    assert await llm.complete_tool("s", "u", spec) is None


@pytest.mark.asyncio
async def test_a_provider_error_degrades_instead_of_raising(env, monkeypatch) -> None:
    """A bad key or wrong model id must not surface to the citizen."""
    env(xai="bad-key")

    def explode(_provider) -> None:
        raise RuntimeError("401 unauthorized")

    monkeypatch.setattr(llm, "_openai_compatible_client", explode)
    assert await llm.complete_text("s", "u") is None


@pytest.mark.asyncio
async def test_extraction_still_works_when_the_model_fails(env, monkeypatch) -> None:
    """The deterministic pass is the floor, not a fallback of last resort."""
    env(xai="bad-key")

    async def broken(*_, **__):
        return None

    monkeypatch.setattr(llm, "complete_tool", broken)
    result = await extraction.extract("meri saalana aay dhai lakh hai", "hi", {})
    values = {f.field: f.value for f in result.accepted}
    assert values["annual_family_income"] == 250000.0


@pytest.mark.asyncio
async def test_explanation_falls_back_to_the_template_when_the_model_fails(
    env, monkeypatch
) -> None:
    env(xai="bad-key")

    async def broken(*_, **__):
        return None

    monkeypatch.setattr(llm, "complete_text", broken)
    result = {
        "scheme_code": "NSFDC_MICRO_FINANCE",
        "official_name": "Micro Finance Scheme",
        "verdict": "ELIGIBLE",
        "indicative_amount": 72000.0,
        "matched_because": [{"rule_id": "MF_CATEGORY_SC", "message": "You are SC."}],
        "blocked_because": [],
        "warnings": [],
    }
    rendered = await explanation.explain(result, "en")
    assert rendered["source"] == "template"
    assert "Micro Finance Scheme" in rendered["explanation"]
    # The rule IDs travel regardless of who wrote the prose.
    assert rendered["rule_ids"] == ["MF_CATEGORY_SC"]


@pytest.mark.asyncio
async def test_explanation_uses_the_model_when_one_answers(env, monkeypatch) -> None:
    env(xai="good-key")

    async def answers(*_, **__):
        return "You can get this loan."

    monkeypatch.setattr(llm, "complete_text", answers)
    rendered = await explanation.explain(
        {"scheme_code": "X", "verdict": "ELIGIBLE", "matched_because": []}, "en"
    )
    assert rendered["source"] == "llm"
    assert rendered["explanation"] == "You can get this loan."


# --- value-level guardrail (a model quirk must never break a turn) ----------------------


def test_lowercase_enum_from_a_model_is_normalised_not_rejected() -> None:
    """A live Groq run returned gender="female"; the contract wants FEMALE. Left alone
    that raised in validate_profile and failed the whole conversational turn."""
    accepted, rejected = extraction._validate_llm_fields(
        {"fields": [{"field": "gender", "value": "female", "confidence": 0.9,
                     "evidence_span": "she"}]}
    )
    assert rejected == []
    assert accepted[0].value == "FEMALE"


def test_a_value_outside_the_vocabulary_is_dropped_not_coerced() -> None:
    accepted, rejected = extraction._validate_llm_fields(
        {"fields": [{"field": "category", "value": "brahmin", "confidence": 0.9,
                     "evidence_span": "x"}]}
    )
    assert accepted == []
    assert rejected == ["category"]


def test_string_booleans_and_numbers_are_coerced() -> None:
    accepted, _ = extraction._validate_llm_fields(
        {"fields": [
            {"field": "is_pwd", "value": "yes", "confidence": 0.9, "evidence_span": "x"},
            {"field": "age", "value": "34", "confidence": 0.9, "evidence_span": "x"},
        ]}
    )
    values = {f.field: f.value for f in accepted}
    assert values["is_pwd"] is True
    assert values["age"] == 34.0


def test_a_district_name_in_any_casing_resolves_to_the_canonical_one() -> None:
    accepted, _ = extraction._validate_llm_fields(
        {"fields": [{"field": "district", "value": "nagpur", "confidence": 0.9,
                     "evidence_span": "x"}]}
    )
    assert accepted[0].value == "Nagpur"


def test_an_unknown_district_is_dropped() -> None:
    accepted, rejected = extraction._validate_llm_fields(
        {"fields": [{"field": "district", "value": "Atlantis", "confidence": 0.9,
                     "evidence_span": "x"}]}
    )
    assert accepted == []
    assert rejected == ["district"]


# --- official scheme names are never machine-translated (CLAUDE.md) --------------------


@pytest.mark.asyncio
async def test_prose_that_renames_the_scheme_is_rejected(env, monkeypatch) -> None:
    """A live Groq run wrote "मिनी फाइनेंस स्कीम" for the Micro Finance Scheme. A legal
    scheme name presented wrong to a citizen is worse than plainer prose."""
    env(groq="gsk-key")

    async def renames(*_, **__):
        return "आप मिनी फाइनेंस स्कीम के लिए पात्र हैं।"

    monkeypatch.setattr(llm, "complete_text", renames)
    rendered = await explanation.explain(
        {
            "scheme_code": "NSFDC_MICRO_FINANCE",
            "official_name": "Micro Finance Scheme",
            "verdict": "ELIGIBLE",
            "matched_because": [],
        },
        "hi",
    )
    assert rendered["source"] == "template"
    assert "Micro Finance Scheme" in rendered["explanation"]


@pytest.mark.asyncio
async def test_prose_that_keeps_the_official_name_is_accepted(env, monkeypatch) -> None:
    env(groq="gsk-key")

    async def keeps(*_, **__):
        return "आप Micro Finance Scheme के लिए पात्र हैं।"

    monkeypatch.setattr(llm, "complete_text", keeps)
    rendered = await explanation.explain(
        {
            "scheme_code": "NSFDC_MICRO_FINANCE",
            "official_name": "Micro Finance Scheme",
            "verdict": "ELIGIBLE",
            "matched_because": [],
        },
        "hi",
    )
    assert rendered["source"] == "llm"


# --- the amount is never the model's to phrase -------------------------------------------

ELIGIBLE_RESULT = {
    "scheme_code": "NSFDC_MICRO_FINANCE",
    "official_name": "Micro Finance Scheme",
    "verdict": "ELIGIBLE",
    "indicative_amount": 72000.0,
    "matched_because": [{"rule_id": "MF_CATEGORY_SC", "message": "You are SC."}],
    "blocked_because": [],
    "warnings": [],
}


@pytest.mark.asyncio
async def test_the_model_is_never_shown_the_amount(env, monkeypatch) -> None:
    """The structural fix: a model that never receives the figure cannot promise it.

    Asserted against what is actually sent, not against the source text.
    """
    env(groq="gsk-key")
    captured: dict[str, str] = {}

    async def capture(system: str, user: str, **__):
        captured["system"] = system
        captured["user"] = user
        return "You qualify for the Micro Finance Scheme."

    monkeypatch.setattr(llm, "complete_text", capture)
    await explanation.explain(ELIGIBLE_RESULT, "en")

    assert "72000" not in captured["user"]
    assert "72,000" not in captured["user"]
    assert "indicative_amount" not in captured["user"]


@pytest.mark.asyncio
async def test_the_amount_sentence_is_appended_by_us_not_the_model(env, monkeypatch) -> None:
    env(groq="gsk-key")

    async def prose(*_, **__):
        return "You qualify for the Micro Finance Scheme because you are SC."

    monkeypatch.setattr(llm, "complete_text", prose)
    rendered = await explanation.explain(ELIGIBLE_RESULT, "en")
    assert rendered["source"] == "llm"
    assert "72,000" in rendered["explanation"]
    assert "may be possible" in rendered["explanation"]


@pytest.mark.asyncio
async def test_prose_claiming_an_approval_is_discarded(env, monkeypatch) -> None:
    """"The loan has been sanctioned" is a decision only a Channel Partner makes."""
    env(groq="gsk-key")

    async def overclaims(*_, **__):
        return "Your Micro Finance Scheme loan has been sanctioned."

    monkeypatch.setattr(llm, "complete_text", overclaims)
    rendered = await explanation.explain(ELIGIBLE_RESULT, "en")
    assert rendered["source"] == "template"


@pytest.mark.asyncio
async def test_hindi_prose_claiming_disbursement_is_discarded(env, monkeypatch) -> None:
    env(groq="gsk-key")

    async def overclaims(*_, **__):
        return "आपको Micro Finance Scheme से पैसा मिल जाएगा।"

    monkeypatch.setattr(llm, "complete_text", overclaims)
    rendered = await explanation.explain(ELIGIBLE_RESULT, "hi")
    assert rendered["source"] == "template"


@pytest.mark.parametrize("language", ["en", "hi"])
def test_our_own_template_never_trips_the_approval_backstop(language: str) -> None:
    """A fallback that its own guard rejects would be an infinite embarrassment."""
    for verdict in ("ELIGIBLE", "LIKELY_ELIGIBLE", "INELIGIBLE", "NEED_MORE_INFO"):
        rendered = explanation.template_explanation(
            {**ELIGIBLE_RESULT, "verdict": verdict}, language
        )
        assert not explanation._claims_approval(rendered), rendered


@pytest.mark.parametrize("language", ["en", "hi"])
def test_no_amount_is_shown_for_an_ineligible_scheme(language: str) -> None:
    assert explanation.amount_sentence({**ELIGIBLE_RESULT, "verdict": "INELIGIBLE"}, language) == ""


# --- internal codes must never reach a citizen -------------------------------------------


def test_a_scheme_code_resolves_to_its_official_name() -> None:
    assert explanation.scheme_display_name("NSFDC_MICRO_FINANCE") == "Micro Finance Scheme"
    assert explanation.scheme_display_name("NSFDC_TERM_LOAN") == "Term Loan"
    assert explanation.scheme_display_name(None) is None


@pytest.mark.parametrize("language", ["en", "hi"])
def test_the_template_redirect_names_the_scheme_not_its_code(language: str) -> None:
    blocked = {
        "scheme_code": "NSFDC_TERM_LOAN",
        "official_name": "Term Loan",
        "verdict": "INELIGIBLE",
        "matched_because": [],
        "blocked_because": [{"rule_id": "TL_PROJECT_COST_FLOOR", "message": "Too small."}],
        "warnings": [],
        "redirect_suggestion": "NSFDC_MICRO_FINANCE",
    }
    rendered = explanation.template_explanation(blocked, language)
    assert "NSFDC_" not in rendered
    assert "Micro Finance Scheme" in rendered


@pytest.mark.asyncio
async def test_the_model_is_never_handed_a_raw_scheme_code(env, monkeypatch) -> None:
    env(groq="gsk-key")
    captured: dict[str, str] = {}

    async def capture(system: str, user: str, **__):
        captured["user"] = user
        return "You could ask about the Micro Finance Scheme."

    monkeypatch.setattr(llm, "complete_text", capture)
    await explanation.explain(
        {
            "scheme_code": "NSFDC_TERM_LOAN",
            "official_name": "Term Loan",
            "verdict": "INELIGIBLE",
            "matched_because": [],
            "blocked_because": [],
            "warnings": [],
            "redirect_suggestion": "NSFDC_MICRO_FINANCE",
        },
        "en",
    )
    assert "NSFDC_" not in captured["user"]
