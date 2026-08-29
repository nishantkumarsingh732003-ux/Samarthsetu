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

    def _set(provider: str = "auto", anthropic: str = "", xai: str = "", model: str = ""):
        monkeypatch.setattr(settings, "LLM_PROVIDER", provider)
        monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", anthropic)
        monkeypatch.setattr(settings, "XAI_API_KEY", xai)
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
    env(xai="xai-super-secret-key", anthropic="ant-super-secret-key")
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

    def explode() -> None:
        raise RuntimeError("401 unauthorized")

    monkeypatch.setattr(llm, "_xai_client", explode)
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
