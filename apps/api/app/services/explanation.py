"""Plain-language explanation of a verdict the rule engine has already reached.

The LLM's entire job here is restatement. It receives the structured
`matched_because` / `blocked_because` reasons and renders them warmly at roughly a
Class 6 reading level. It is told, in the system prompt, that it may not add, infer or
soften any eligibility conclusion — and structurally it cannot, because it is called
*after* the verdict exists and its output never feeds back into it.

The raw rule IDs travel alongside the prose so the UI can offer "see the exact rule".

With no API key, or if the model call fails or times out, a deterministic template
produces the paragraph instead. The product must read correctly with the LLM entirely
offline; that is the Phase 7 requirement, met here rather than bolted on later.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

EXPLANATION_SYSTEM_PROMPT = """You explain a government credit-scheme decision to an \
applicant in India who may read at about a Class 6 level.

You may only restate the reasons provided. You may not add, infer, or soften any \
eligibility conclusion. You may not invent amounts, interest rates, timelines, \
documents, or next steps that are not in the input.

Write two or three short sentences in the requested language. Be warm and direct. Do \
not use bullet points, headings, or markdown. Do not mention that you are an AI, and \
do not mention rules, engines, or systems — speak plainly about the person's own \
situation.

If the applicant is not eligible for something, say so kindly and state the reason \
given, without suggesting the decision might change."""


def _verdict_sentence(result: dict[str, Any], language: str) -> str:
    name = result.get("official_name", result.get("scheme_code", ""))
    verdict = result.get("verdict")
    amount = result.get("indicative_amount")

    if language == "hi":
        if verdict in {"ELIGIBLE", "LIKELY_ELIGIBLE"}:
            base = f"आप {name} के लिए पात्र हैं।"
            if amount:
                base += f" इसके तहत लगभग Rs {amount:,.0f} तक का ऋण मिल सकता है।"
            return base
        if verdict == "NEED_MORE_INFO":
            return f"{name} के बारे में बताने के लिए हमें कुछ और जानकारी चाहिए।"
        return f"अभी आप {name} के लिए पात्र नहीं हैं।"

    if verdict in {"ELIGIBLE", "LIKELY_ELIGIBLE"}:
        base = f"You are eligible for the {name}."
        if amount:
            base += f" It could provide about Rs {amount:,.0f}."
        return base
    if verdict == "NEED_MORE_INFO":
        return f"We need a little more information before we can tell you about the {name}."
    return f"You are not eligible for the {name} right now."


def template_explanation(result: dict[str, Any], language: str = "en") -> str:
    """Deterministic fallback. Restates the engine's own reasons, nothing more."""
    parts = [_verdict_sentence(result, language)]

    blocked = result.get("blocked_because") or []
    matched = result.get("matched_because") or []
    warnings = result.get("warnings") or []

    if blocked:
        parts.append(" ".join(r["message"] for r in blocked))
        redirect = result.get("redirect_suggestion")
        if redirect:
            parts.append(
                f"आप {redirect} के बारे में पूछ सकते हैं।"
                if language == "hi"
                else f"You may want to ask about the {redirect} instead."
            )
    elif matched:
        # Two reasons is enough for a paragraph; the full list stays in the response.
        parts.append(" ".join(r["message"] for r in matched[:2]))

    if warnings:
        parts.append(" ".join(r["message"] for r in warnings))

    if result.get("verdict") == "NEED_MORE_INFO":
        missing = result.get("missing_fields") or []
        if missing:
            readable = ", ".join(m.replace("_", " ") for m in missing)
            parts.append(
                f"हमें यह जानना है: {readable}."
                if language == "hi"
                else f"We still need to know: {readable}."
            )

    return " ".join(p for p in parts if p).strip()


def llm_available() -> bool:
    return bool(settings.ANTHROPIC_API_KEY.strip())


async def explain(result: dict[str, Any], language: str = "en") -> dict[str, Any]:
    """Render one scheme result as prose, with the rule IDs kept alongside."""
    rule_ids = [
        r["rule_id"]
        for key in ("matched_because", "blocked_because", "warnings")
        for r in (result.get(key) or [])
    ]

    payload = {
        "scheme_code": result.get("scheme_code"),
        "verdict": result.get("verdict"),
        "rule_ids": rule_ids,
        "language": language,
    }

    if not llm_available():
        return {**payload, "explanation": template_explanation(result, language),
                "source": "template"}

    try:
        from anthropic import AsyncAnthropic

        reasons = {
            "scheme": result.get("official_name"),
            "verdict": result.get("verdict"),
            "indicative_amount": result.get("indicative_amount"),
            "matched_because": [r["message"] for r in result.get("matched_because") or []],
            "blocked_because": [r["message"] for r in result.get("blocked_because") or []],
            "warnings": [r["message"] for r in result.get("warnings") or []],
            "redirect_suggestion": result.get("redirect_suggestion"),
        }
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = await client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=400,
            system=EXPLANATION_SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Language: {language}\n"
                        f"Decision to restate:\n{reasons}"
                    ),
                }
            ],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        ).strip()
        if text:
            return {**payload, "explanation": text, "source": "llm"}
    except Exception as exc:  # noqa: BLE001 - never let the explainer break the verdict
        logger.warning("explanation LLM unavailable, using template: %s", exc)

    return {**payload, "explanation": template_explanation(result, language),
            "source": "template"}
