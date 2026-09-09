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

from app.services import llm

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
given, without suggesting the decision might change.

CRITICAL: this service does not approve, sanction, or disburse anything. It only tells
the applicant which scheme fits and which Channel Partner can process it; a Channel
Partner decides the loan. Never write that anything is approved, sanctioned, granted,
released or guaranteed, and never say the applicant will receive money.

CRITICAL: do not mention any rupee amount. You are not given one. The amount is added
separately, in wording this service controls.

CRITICAL: the scheme name is a legal name. Reproduce it EXACTLY as given, in the Latin \
script, even when writing in another language. Never translate it, transliterate it, \
shorten it, or substitute a similar-sounding name."""


def scheme_display_name(code: str | None) -> str | None:
    """Resolve an internal scheme code to the official name a citizen should read.

    `redirect_suggestion` carries a code like NSFDC_MICRO_FINANCE. Passed through
    unresolved it reaches the citizen verbatim — a live run rendered "आपको
    NSFDC_MICRO_FINANCE योजना के लिए ... विचार करना चाहिए" — which is both unreadable and
    not the scheme's legal name.
    """
    if not code:
        return None
    try:
        from setu_rules import load_schemes

        for scheme in load_schemes():
            if scheme.code == code:
                return scheme.official_name
    except Exception:  # noqa: BLE001 - a display nicety must never break an explanation
        logger.warning("could not resolve scheme code %r to a name", code)
    return code


def _preserves_scheme_name(text: str, result: dict[str, Any]) -> bool:
    """Reject prose that renamed the scheme.

    CLAUDE.md forbids machine-translating official scheme names. A live Groq run
    returned "मिनी फाइनेंस स्कीम" for the Micro Finance Scheme — a different scheme name,
    stated to a citizen as fact. Instructing the model is not enough, so the output is
    checked and dropped to the template if the name did not survive.
    """
    official = (result.get("official_name") or "").strip()
    return not official or official in text


def amount_sentence(result: dict[str, Any], language: str) -> str:
    """The money sentence, always written by us and never by a model.

    A language model handed a rupee figure will eventually phrase it as a promise —
    a live run produced "the amount can now be released", which claims a sanction this
    service never makes. Removing the number from what the model sees makes that class
    of error unreachable rather than merely discouraged.
    """
    amount = result.get("indicative_amount")
    if not amount or result.get("verdict") not in {"ELIGIBLE", "LIKELY_ELIGIBLE"}:
        return ""
    return ui_string("amount", language).format(amount=f"{amount:,.0f}")


# English and Hindi are maintained here because they are the reviewed languages; every
# other language is served from packages/rules/translations/<lang>.yaml.
UI_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "eligible": "You are eligible for the {scheme}.",
        "need_more_info": (
            "We need a little more information before we can tell you about the {scheme}."
        ),
        "ineligible": "You are not eligible for the {scheme} right now.",
        "amount": "Under this scheme a loan of up to about Rs {amount} may be possible.",
        "redirect": "You may want to ask about the {scheme} instead.",
        "still_need": "We still need to know: {fields}.",
        # The assistant's reply when no model is configured or the call failed. It
        # points at the screen that holds the answer rather than apologising, because
        # `LLM_PROVIDER=none` is a supported configuration and not an outage.
        "assistant_offline": (
            "From your answers the {scheme} fits. Open it to see the rule that decided "
            "and the partners authorised to process it."
        ),
        "assistant_offline_none": (
            "I do not have that answer here. Your scheme results carry the same "
            "information, with the rule that decided each one."
        ),
    },
    "hi": {
        "eligible": "आप {scheme} के लिए पात्र हैं।",
        "need_more_info": "{scheme} के बारे में बताने के लिए हमें कुछ और जानकारी चाहिए।",
        "ineligible": "अभी आप {scheme} के लिए पात्र नहीं हैं।",
        "amount": "इस योजना के तहत अधिकतम लगभग Rs {amount} तक का ऋण संभव है।",
        "redirect": "आप {scheme} के बारे में पूछ सकते हैं।",
        "still_need": "हमें यह जानना है: {fields}।",
        "assistant_offline": (
            "आपके उत्तरों के अनुसार {scheme} आपके लिए उपयुक्त है। इसे खोलकर वह नियम देखें "
            "जिसने यह तय किया, और वे साझेदार जो इसे संसाधित कर सकते हैं।"
        ),
        "assistant_offline_none": (
            "इसका उत्तर मेरे पास यहाँ नहीं है। आपके योजना परिणामों में यही जानकारी है, "
            "और साथ में वह नियम भी जिसने हर एक को तय किया।"
        ),
    },
}


def ui_string(key: str, language: str) -> str:
    """One UI string: inline table first, then the language bundle, English last."""
    inline = UI_STRINGS.get(language, {}).get(key)
    if inline:
        return inline
    try:
        from setu_rules import bundle_for

        bundle = bundle_for(language)
        if bundle and bundle.ui.get(key):
            return bundle.ui[key]
    except Exception:  # noqa: BLE001 - a missing bundle must never break an explanation
        logger.warning("translation bundle unavailable for %r", language)
    return UI_STRINGS["en"][key]


# Words that assert a decision this service does not make. The structural fix above
# (withholding the amount) removes the common case; this is a backstop for prose that
# claims an approval without quoting a figure. Deliberately narrow: a false positive
# only costs a fall back to the template, which is always correct.
APPROVAL_CLAIMS: tuple[str, ...] = (
    "approved", "sanctioned", "disbursed", "has been granted", "is released",
    "will receive", "will get", "guaranteed",
    "स्वीकृत", "मंजूर", "मंज़ूर", "जारी कर", "मिल जाएगा", "मिलेगा", "गारंटी",
)


def approval_claims_for(language: str) -> tuple[str, ...]:
    """English and Hindi terms always apply — model prose mixes scripts freely — plus
    whatever the requested language's bundle declares."""
    extra: tuple[str, ...] = ()
    try:
        from setu_rules import bundle_for

        bundle = bundle_for(language)
        if bundle:
            extra = bundle.approval_claims
    except Exception:  # noqa: BLE001
        logger.warning("could not load approval claims for %r", language)
    return APPROVAL_CLAIMS + extra


def _claims_approval(text: str, language: str = "en") -> bool:
    lowered = text.lower()
    return any(claim.lower() in lowered for claim in approval_claims_for(language))


def _verdict_sentence(result: dict[str, Any], language: str) -> str:
    name = result.get("official_name", result.get("scheme_code", ""))
    verdict = result.get("verdict")
    key = (
        "eligible"
        if verdict in {"ELIGIBLE", "LIKELY_ELIGIBLE"}
        else "need_more_info"
        if verdict == "NEED_MORE_INFO"
        else "ineligible"
    )
    return ui_string(key, language).format(scheme=name)


def template_explanation(result: dict[str, Any], language: str = "en") -> str:
    """Deterministic fallback. Restates the engine's own reasons, nothing more."""
    parts = [_verdict_sentence(result, language)]

    blocked = result.get("blocked_because") or []
    matched = result.get("matched_because") or []
    warnings = result.get("warnings") or []

    if blocked:
        parts.append(" ".join(r["message"] for r in blocked))
        redirect = scheme_display_name(result.get("redirect_suggestion"))
        if redirect:
            parts.append(ui_string("redirect", language).format(scheme=redirect))
    elif matched:
        # Two reasons is enough for a paragraph; the full list stays in the response.
        parts.append(" ".join(r["message"] for r in matched[:2]))

    if warnings:
        parts.append(" ".join(r["message"] for r in warnings))

    if result.get("verdict") == "NEED_MORE_INFO":
        missing = result.get("missing_fields") or []
        if missing:
            readable = ", ".join(m.replace("_", " ") for m in missing)
            parts.append(ui_string("still_need", language).format(fields=readable))

    parts.append(amount_sentence(result, language))
    return " ".join(p for p in parts if p).strip()


def llm_available() -> bool:
    return llm.is_available()


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

    # The model is handed the engine's own reasons and nothing else. It has no access
    # to the profile, the rules, or any way to reach a different conclusion.
    reasons = {
        "scheme": result.get("official_name"),
        "verdict": result.get("verdict"),
        # indicative_amount is deliberately absent — see amount_sentence().
        "matched_because": [r["message"] for r in result.get("matched_because") or []],
        "blocked_because": [r["message"] for r in result.get("blocked_because") or []],
        "warnings": [r["message"] for r in result.get("warnings") or []],
        # Resolved to the official name: the model must never be handed an internal
        # code, because it will faithfully print it to the citizen.
        "redirect_suggestion": scheme_display_name(result.get("redirect_suggestion")),
    }

    text = await llm.complete_text(
        system=EXPLANATION_SYSTEM_PROMPT,
        user=f"Language: {language}\nDecision to restate:\n{reasons}",
        max_tokens=400,
    )
    if text and not _preserves_scheme_name(text, result):
        logger.warning(
            "explanation dropped: model altered the official scheme name %r",
            result.get("official_name"),
        )
        text = None

    if text and _claims_approval(text, language):
        logger.warning("explanation dropped: model implied an approval or disbursement")
        text = None

    if text:
        # The money sentence is appended by us, in wording we control.
        combined = " ".join(p for p in (text, amount_sentence(result, language)) if p)
        return {**payload, "explanation": combined, "source": "llm"}

    return {
        **payload,
        "explanation": template_explanation(result, language),
        "source": "template",
    }
