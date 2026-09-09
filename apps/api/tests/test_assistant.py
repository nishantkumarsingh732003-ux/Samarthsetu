"""The grounded question-answering assistant.

`services/assistant.py` states three guarantees in its own docstring: it never decides
eligibility, it answers only from the context pack, and it proposes actions rather than
taking them. Until now nothing held it to any of them — the module and the
`/conversation/ask` route that fronts it shipped with no coverage at all, which is how a
fallback that returns an empty string sat in the tree looking like a working feature.

These are pure-function tests over the pack. No database, no network, and no model: the
suite-wide `no_live_llm` fixture in conftest.py already forces `LLM_PROVIDER=none`, so
`answer()` takes the fallback path unless a test patches `llm` explicitly.
"""

from __future__ import annotations

import json

import pytest

from app.services import assistant


def _scheme(code: str = "NSFDC_MF", **overrides) -> dict:
    scheme = {
        "code": code,
        "official_name": "Micro Finance Scheme",
        "family": "MICRO_FINANCE",
        "limits": {"max_loan": 140000},
        "authorised_partner_count": 12,
        "rules": [
            {
                "rule_id": "MF_INCOME_CEILING",
                "severity": "BLOCKER",
                "message": "Annual family income must not exceed Rs 5,00,000.",
            }
        ],
        "required_documents": [{"name": "Caste certificate"}],
    }
    scheme.update(overrides)
    return scheme


def _verdict(code: str = "NSFDC_MF", verdict: str = "ELIGIBLE", **overrides) -> dict:
    result = {
        "scheme_code": code,
        "verdict": verdict,
        "indicative_amount": 120000,
        "matched_because": [{"rule_id": "MF_INCOME_CEILING", "message": "Within ceiling."}],
        "blocked_because": [],
    }
    result.update(overrides)
    return result


def _pack(**overrides) -> str:
    kwargs = {
        "profile": {"annual_family_income": 200000, "project_cost": 120000},
        "schemes": [_scheme()],
        "results": [_verdict()],
        "applications": None,
    }
    kwargs.update(overrides)
    return assistant.build_context(**kwargs)


# --- the pack ------------------------------------------------------------------------


def test_pack_carries_the_engine_verdict_and_the_rule_ids_that_produced_it() -> None:
    """CLAUDE.md rule 1 and 3: the model restates a verdict it can cite, or nothing.

    A pack that carried the schemes but not the verdicts would leave the model with no
    honest way to answer "am I eligible?" — and an eligibility question with no verdict
    in front of it is precisely the situation where a model invents one.
    """
    pack = json.loads(_pack())

    assert pack["engine_verdicts"] == [
        {
            "scheme_code": "NSFDC_MF",
            "verdict": "ELIGIBLE",
            "indicative_amount": 120000,
            "matched_because": ["MF_INCOME_CEILING"],
            "blocked_because": [],
        }
    ]


def test_pack_carries_the_reason_text_for_every_block() -> None:
    """`blocked_because` keeps its message where `matched_because` keeps only the id.

    Asymmetric on purpose: telling someone why they were turned away is the product, and
    the reason has to reach the model as words it can translate.
    """
    blocked = _verdict(
        verdict="INELIGIBLE",
        matched_because=[],
        blocked_because=[
            {"rule_id": "MF_INCOME_CEILING", "message": "Income above Rs 5,00,000."}
        ],
    )
    pack = json.loads(_pack(results=[blocked]))

    assert pack["engine_verdicts"][0]["blocked_because"] == [
        {"rule_id": "MF_INCOME_CEILING", "reason": "Income above Rs 5,00,000."}
    ]


@pytest.mark.parametrize(
    "field, value",
    [
        ("display_name", "Rahul Kumar"),
        ("email", "rahul@example.com"),
        ("aadhaar_last4", "4321"),
        ("aadhaar_hash", "9f2c" * 16),
        ("phone", "9876500000"),
        ("business_name", "Kumar Tailoring Unit"),
    ],
)
def test_identifying_fields_never_reach_the_provider(field: str, value: str) -> None:
    """DPDP rule 4. `build_context` is an allow-list, and this is what keeps it one.

    What goes to a third-party inference provider is a decision, not an accident. A
    profile that grows a field later must not carry it out of the country by default.
    """
    context = _pack(profile={"annual_family_income": 200000, field: value})

    assert value not in context
    assert field not in json.loads(context)["profile"]


def test_absent_profile_fields_are_dropped_rather_than_sent_as_null() -> None:
    """A null in the pack reads to a model as a known-empty fact, not an unknown one."""
    pack = json.loads(_pack(profile={"annual_family_income": 200000, "district": None}))

    assert pack["profile"] == {"annual_family_income": 200000}


def test_applications_are_included_only_when_the_citizen_has_them() -> None:
    assert "my_applications" not in json.loads(_pack())

    with_app = json.loads(
        _pack(
            applications=[
                {
                    "reference_no": "SS-2026-000123",
                    "scheme_name": "Micro Finance Scheme",
                    "status": "DOCUMENTS_PENDING",
                    "documents_outstanding": 2,
                }
            ]
        )
    )
    assert with_app["my_applications"][0]["reference_no"] == "SS-2026-000123"


# --- the transcript ------------------------------------------------------------------


def test_transcript_keeps_only_the_recent_turns() -> None:
    """Bounded on purpose: the pack is already large and every token is billed."""
    history = [{"role": "citizen", "text": f"turn {n}"} for n in range(20)]
    lines = assistant._transcript(history).splitlines()

    assert len(lines) == 8
    assert lines[-1] == "Citizen: turn 19"


def test_transcript_clips_a_pasted_paragraph() -> None:
    """One long message must not crowd the pack out of the context window."""
    history = [{"role": "citizen", "text": "x" * 5000}]

    assert len(assistant._transcript(history)) < 500


def test_transcript_labels_each_side() -> None:
    history = [
        {"role": "citizen", "text": "what documents?"},
        {"role": "assistant", "text": "A caste certificate."},
    ]

    assert assistant._transcript(history) == (
        "Citizen: what documents?\nAssistant: A caste certificate."
    )


# --- answering -----------------------------------------------------------------------


@pytest.mark.anyio
async def test_without_a_model_the_reply_still_says_something() -> None:
    """The whole product works with `LLM_PROVIDER=none`, and this path is why.

    The fallback is not an apology and not a blank bubble: it points at the screen that
    holds the answer, in the citizen's language, and carries the rule ids the engine
    actually used. A caller that receives an empty string has nothing to render.
    """
    result = await assistant.answer("am I eligible?", _pack(), "en")

    assert result.grounded is False
    assert result.text.strip(), "the fallback must produce a reply, not an empty string"
    assert result.action == "open_scheme"
    assert result.action_scheme_code == "NSFDC_MF"
    assert "MF_INCOME_CEILING" in result.rule_ids


@pytest.mark.anyio
async def test_the_fallback_never_claims_an_eligibility_it_was_not_given() -> None:
    """With every scheme blocked there is no scheme to offer, so none is offered."""
    blocked = _verdict(
        verdict="INELIGIBLE",
        matched_because=[],
        blocked_because=[{"rule_id": "MF_INCOME_CEILING", "message": "Income too high."}],
    )

    result = await assistant.answer("am I eligible?", _pack(results=[blocked]), "en")

    assert result.grounded is False
    assert result.text.strip()
    assert result.action is None
    assert result.action_scheme_code is None


@pytest.mark.anyio
async def test_an_action_the_client_cannot_render_is_dropped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The enum is advisory to the model. A value outside it is a button going nowhere.

    Dropping it here rather than in the client keeps every caller — the web thread, the
    WhatsApp path — from having to know the set independently.
    """

    async def _reply(**_kwargs):
        return {
            "answer": "You can apply through a Channel Partner.",
            "rule_ids": ["MF_INCOME_CEILING"],
            "action": "approve_loan",
            "action_scheme_code": "NSFDC_MF",
        }

    monkeypatch.setattr(assistant.llm, "is_available", lambda: True)
    monkeypatch.setattr(assistant.llm, "complete_tool", _reply)

    result = await assistant.answer("how do I apply?", _pack(), "en")

    assert result.grounded is True
    assert result.action is None
    assert result.text == "You can apply through a Channel Partner."


@pytest.mark.anyio
async def test_a_model_that_answers_with_nothing_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A reasoning model that spends its budget before writing looks like an outage.

    Either way the citizen must get a reply, so an empty answer takes the same path as
    an unreachable provider rather than rendering as silence.
    """

    async def _empty(**_kwargs):
        return {"answer": "   ", "action": "none"}

    monkeypatch.setattr(assistant.llm, "is_available", lambda: True)
    monkeypatch.setattr(assistant.llm, "complete_tool", _empty)

    result = await assistant.answer("am I eligible?", _pack(), "en")

    assert result.grounded is False
    assert result.text.strip()


@pytest.mark.anyio
async def test_the_system_prompt_is_given_the_citizens_language(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rule 4 of the prompt. A Hindi speaker getting an English answer is the failure."""
    seen: dict[str, str] = {}

    async def _capture(*, system: str, user: str, **_kwargs):
        seen["system"] = system
        seen["user"] = user
        return {"answer": "haan", "action": "none"}

    monkeypatch.setattr(assistant.llm, "is_available", lambda: True)
    monkeypatch.setattr(assistant.llm, "complete_tool", _capture)

    await assistant.answer("kya main eligible hoon?", _pack(), "hi")

    assert "hi" in seen["system"]
    assert "{language}" not in seen["system"]
    # The pack, and only the pack, is what the model reads the answer out of.
    assert "MF_INCOME_CEILING" in seen["user"]
    assert "kya main eligible hoon?" in seen["user"]


@pytest.mark.anyio
async def test_earlier_turns_are_offered_to_the_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """So that "and the interest?" resolves instead of becoming a clarifying question."""
    seen: dict[str, str] = {}

    async def _capture(*, user: str, **_kwargs):
        seen["user"] = user
        return {"answer": "6.5% per annum.", "action": "none"}

    monkeypatch.setattr(assistant.llm, "is_available", lambda: True)
    monkeypatch.setattr(assistant.llm, "complete_tool", _capture)

    await assistant.answer(
        "and the interest?",
        _pack(),
        "en",
        history=[{"role": "citizen", "text": "tell me about the Micro Finance Scheme"}],
    )

    assert "tell me about the Micro Finance Scheme" in seen["user"]


@pytest.mark.anyio
@pytest.mark.parametrize("language", ["en", "hi", "mr", "bn", "ta", "te"])
async def test_the_fallback_speaks_every_supported_language(language: str) -> None:
    """A Hindi speaker with no model configured still gets Hindi, not English.

    The strings resolve through `explanation.ui_string`, so `en`/`hi` come from the
    reviewed inline table and the rest from their bundle. A language whose bundle has
    not been written yet falls back to English rather than failing — which is why this
    asserts the scheme name survives rather than asserting a particular script.
    """
    result = await assistant.answer("am I eligible?", _pack(), language)

    assert result.text.strip()
    # The legal name, verbatim and in Latin script, never the internal code.
    assert "Micro Finance Scheme" in result.text
    assert "NSFDC_MF" not in result.text


@pytest.mark.anyio
async def test_the_fallback_names_the_scheme_not_its_code() -> None:
    """`redirect_suggestion` shipped a raw code to a citizen once. Not again."""
    result = await assistant.answer("which one?", _pack(), "en")

    assert "Micro Finance Scheme" in result.text


def test_an_application_reaches_the_pack_with_its_outstanding_document_count() -> None:
    """"What documents do I still need?" is a suggested prompt on the page.

    The route assembles the pack from the same `/citizen/applications` projection the
    tracking screen uses. If the applications stop arriving, the prompt cannot be
    answered from the pack, and the system prompt then correctly refuses to guess — so
    the visible symptom is the assistant claiming not to know about the citizen's own
    application.
    """
    pack = json.loads(
        _pack(
            applications=[
                {
                    "reference_no": "SS-2026-000123",
                    "scheme_name": "Micro Finance Scheme",
                    "status": "DOCUMENTS_PENDING",
                    "documents_outstanding": 2,
                }
            ]
        )
    )

    assert pack["my_applications"] == [
        {
            "reference_no": "SS-2026-000123",
            "scheme_name": "Micro Finance Scheme",
            "status": "DOCUMENTS_PENDING",
            "documents_outstanding": 2,
        }
    ]


def test_the_prompt_forbids_translating_a_legal_scheme_name() -> None:
    """CLAUDE.md: official names stay verbatim, with a gloss if one helps.

    Observed failing before this rule existed — asked in Hindi, the model replied with
    transliterations of the legal names. A citizen who walks into a bank asking for a
    name that appears on no circular is the misrouting this product exists to prevent.
    """
    prompt = assistant.SYSTEM.format(language="hi")

    assert "official_name" in prompt
    assert "Latin script" in prompt
    assert "Never translate it, transliterate it" in prompt


def test_the_prompt_states_that_the_engine_decides_not_the_model() -> None:
    """CLAUDE.md rule 1, asserted where it is actually enforced — in the words."""
    prompt = assistant.SYSTEM.format(language="en")

    assert "do NOT decide eligibility" in prompt
    assert "deterministic rule engine" in prompt
    assert "Never promise approval" in prompt
