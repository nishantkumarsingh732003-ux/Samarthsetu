"""Grounded question answering for the citizen assistant.

WHAT THIS IS FOR. `conversation.handle_turn` is an *intake*: it extracts facts and runs
the rule engine, one question at a time. It cannot answer "what documents do I need?" or
"why was this one recommended?" because answering was never its job. This module is that
job — a model reading a context pack assembled from real data and answering in the
citizen's own language.

THE THREE RULES IT WORKS UNDER, in the order they matter.

1. It never decides eligibility. CLAUDE.md rule 1. The verdicts in the context pack come
   from the deterministic engine, carry their rule ids, and the system prompt forbids the
   model from reaching its own. A question about eligibility is answered by restating
   what the engine already decided — the same guarantee the explanation path gives.

2. It answers only from the pack. Every scheme figure, rule, document and partner count
   handed to the model comes out of the rule pack or the database in this request. The
   prompt says to answer "I don't know" rather than fill a gap, because the alternative
   on a page carrying a ministry's name is a confidently invented loan term.

3. It proposes actions; it does not take them. The model may return an `action` naming
   something the citizen could do next — open a scheme, start an application, upload a
   document. The client renders it as a button the citizen presses. Nothing here submits
   an application, and nothing here writes. An assistant that could file for government
   credit on its own reading of a sentence is not a feature.

With no model configured the endpoint still answers: `fallback_answer` builds a reply
from the same pack deterministically. That is the same posture as the rest of the product
— the model makes the words better and is never load-bearing.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from app.services import llm
from app.services._system_prompt import SYSTEM

logger = logging.getLogger(__name__)

# What the assistant may suggest the citizen does next. Each maps to a screen that
# already exists; the client turns it into a button. Deliberately small — an action the
# UI cannot render is a promise the citizen cannot act on.
ACTIONS = (
    "open_scheme",
    "find_partners",
    "start_application",
    "upload_documents",
    "plan_repayment",
)

ANSWER_TOOL = llm.ToolSpec(
    name="answer",
    description=(
        "Answer the citizen's question using only the provided context. "
        "Optionally propose one next step they could take."
    ),
    parameters={
        "type": "object",
        "properties": {
            "answer": {
                "type": "string",
                "description": (
                    "The reply, in the citizen's language. Plain sentences, no markdown. "
                    "Cite rule ids like MF_INCOME_CEILING when a rule decided something."
                ),
            },
            "rule_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Rule ids the answer relies on. Empty if none apply.",
            },
            "action": {
                "type": "string",
                "enum": [*ACTIONS, "none"],
                "description": "One next step the citizen could take, or 'none'.",
            },
            "action_scheme_code": {
                "type": "string",
                "description": "Scheme code the action applies to, if any.",
            },
        },
        "required": ["answer", "action"],
    },
)



@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    rule_ids: list[str]
    action: str | None
    action_scheme_code: str | None
    grounded: bool
    """False when no model was available and the deterministic reply was used."""


def build_context(
    *,
    profile: dict[str, Any],
    schemes: list[dict[str, Any]],
    results: list[dict[str, Any]] | None,
    applications: list[dict[str, Any]] | None,
) -> str:
    """The pack the model is allowed to read, as compact JSON.

    Deliberately assembled here rather than handed the raw ORM rows: what reaches a
    third-party inference provider is a decision, not an accident. Nothing personally
    identifying beyond what the citizen typed about their own project goes in — no
    name, no email, no document images, no Aadhaar of any length.
    """
    pack: dict[str, Any] = {
        "profile": {
            key: profile.get(key)
            for key in (
                "category",
                "annual_family_income",
                "project_cost",
                "project_sector",
                "loan_required",
                "own_contribution",
                "district",
                "state",
                "business_status",
                "admission_confirmed",
            )
            if profile.get(key) is not None
        },
        "schemes": [
            {
                "code": scheme["code"],
                "official_name": scheme["official_name"],
                "family": scheme["family"],
                "limits": scheme["limits"],
                "authorised_partner_count": scheme.get("authorised_partner_count"),
                "rules": [
                    {
                        "id": rule["rule_id"],
                        "severity": rule["severity"],
                        "requirement": rule["message"],
                    }
                    for rule in scheme.get("rules", [])
                ],
                "documents": [doc["name"] for doc in scheme.get("required_documents", [])],
            }
            for scheme in schemes
        ],
    }

    if results:
        pack["engine_verdicts"] = [
            {
                "scheme_code": result["scheme_code"],
                "verdict": result["verdict"],
                "indicative_amount": result.get("indicative_amount"),
                "matched_because": [r["rule_id"] for r in result.get("matched_because", [])],
                "blocked_because": [
                    {"rule_id": r["rule_id"], "reason": r["message"]}
                    for r in result.get("blocked_because", [])
                ],
            }
            for result in results
        ]

    if applications:
        pack["my_applications"] = [
            {
                "reference_no": app["reference_no"],
                "scheme_name": app["scheme_name"],
                "status": app["status"],
                "documents_outstanding": app["documents_outstanding"],
            }
            for app in applications
        ]

    return json.dumps(pack, ensure_ascii=False, separators=(",", ":"))


def _transcript(history: list[dict[str, str]] | None) -> str:
    """The recent turns, as the model should read them.

    Bounded on purpose. The context pack is already large, every token is billed, and a
    citizen resolving "it" or "the interest" needs the last few exchanges — not the
    whole session. Oldest are dropped first, and each line is clipped so one pasted
    paragraph cannot crowd out the pack.
    """
    if not history:
        return ""
    recent = history[-8:]
    lines = [
        f"{'Citizen' if turn.get('role') == 'citizen' else 'Assistant'}: "
        f"{(turn.get('text') or '')[:400]}"
        for turn in recent
        if (turn.get("text") or "").strip()
    ]
    return "\n".join(lines)


async def answer(
    question: str,
    context: str,
    language: str,
    history: list[dict[str, str]] | None = None,
) -> Answer:
    """Answer from the pack, or fall back to a deterministic reply."""
    if not llm.is_available():
        return fallback_answer(context, language)

    # Generous budget: Groq's reasoning models spend it before writing anything, and a
    # truncated answer about a loan term is worse than a slow one. See `complete_tool`.
    payload = await llm.complete_tool(
        system=SYSTEM.format(language=language),
        user=(
            f"CONTEXT:\n{context}\n\n"
            + (
                f"EARLIER IN THIS CONVERSATION:\n{_transcript(history)}\n\n"
                if history
                else ""
            )
            + f"CITIZEN'S QUESTION:\n{question}"
        ),
        tool=ANSWER_TOOL,
        max_tokens=2048,
    )
    # `.strip()` before the test, not after: a reasoning model that spends its budget
    # before writing returns whitespace, which is truthy. Without this the caller gets
    # `grounded=True` with nothing in it and renders an empty chat bubble — the failure
    # is indistinguishable from the model having answered.
    text = str(payload.get("answer") or "").strip() if payload else ""
    if not text:
        logger.info("assistant: model gave no answer, falling back")
        return fallback_answer(context, language)

    action = payload.get("action")
    return Answer(
        text=text,
        rule_ids=[str(r) for r in payload.get("rule_ids") or []],
        # The enum is advisory to the model, not enforced by it — a value outside the
        # set would render as a button that goes nowhere, so it is dropped here.
        action=action if action in ACTIONS else None,
        action_scheme_code=payload.get("action_scheme_code") or None,
        grounded=True,
    )


def fallback_answer(context: str, language: str = "en") -> Answer:
    """The reply when no model is configured, or the call failed.

    Not an apology, and not a blank bubble: it names the scheme the engine actually
    matched, in the citizen's language, and points at the screen that holds the rest.
    The whole product works with `LLM_PROVIDER=none`, and this path is why — so it has
    to read as an answer rather than as a degraded one. `LLM_PROVIDER=none` is a
    supported configuration, so the wording never claims an outage.

    It stays inside the same guarantee as the model path: the verdict is the engine's,
    the rule ids come from the pack, and no scheme is offered unless the engine left one
    usable.
    """
    # Imported here rather than at module scope: `explanation` owns the language
    # resolution (inline table, then the bundle, then English) and importing it at the
    # top would tie this module's import order to it for one string.
    from app.services.explanation import ui_string

    pack = json.loads(context)
    verdicts = pack.get("engine_verdicts") or []
    usable = [v for v in verdicts if v["verdict"] != "INELIGIBLE"]

    if usable:
        code = usable[0]["scheme_code"]
        # The legal name, never the internal code — CLAUDE.md keeps official names
        # verbatim, and a citizen reading "NSFDC_MICRO_FINANCE" learns nothing.
        name = next(
            (s["official_name"] for s in pack.get("schemes", []) if s["code"] == code),
            code,
        )
        return Answer(
            text=ui_string("assistant_offline", language).format(scheme=name),
            rule_ids=[rid for v in usable for rid in v["matched_because"]],
            action="open_scheme",
            action_scheme_code=code,
            grounded=False,
        )
    return Answer(
        text=ui_string("assistant_offline_none", language),
        rule_ids=[],
        action=None,
        action_scheme_code=None,
        grounded=False,
    )
