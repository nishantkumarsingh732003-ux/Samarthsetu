"""Provider-agnostic language model client.

Two operations, because that is all this product asks of a model:

  - `complete_text`  — restate a decision the rule engine has already made
  - `complete_tool`  — extract structured facts under a fixed JSON schema

Neither can affect a verdict. Extraction runs before the rule engine and only proposes
candidate facts; explanation runs after it and only restates its reasons. That is why
the provider is genuinely swappable and why `none` is a supported configuration rather
than a degraded one — with no key at all, the deterministic parser carries extraction
and templates carry explanations.

Every failure path returns None. A wrong model id, an expired key, a timeout, a network
partition and a provider outage all look the same to callers: no answer, fall back.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class Provider(StrEnum):
    NONE = "none"
    ANTHROPIC = "anthropic"
    XAI = "xai"


# Used when LLM_MODEL is blank. Model names change; `scripts/check_llm.py` reports what
# the configured provider actually accepted.
DEFAULT_MODELS: dict[Provider, str] = {
    Provider.ANTHROPIC: "claude-sonnet-5",
    Provider.XAI: "grok-4",
}


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """One tool, in a neutral shape both provider SDKs can be given."""

    name: str
    description: str
    parameters: dict[str, Any]

    def as_anthropic(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }

    def as_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


def resolve_provider() -> Provider:
    """Which provider this deployment will use, honouring an explicit override."""
    configured = (settings.LLM_PROVIDER or "auto").strip().lower()

    if configured == "none":
        return Provider.NONE
    if configured == "anthropic":
        return Provider.ANTHROPIC if settings.ANTHROPIC_API_KEY.strip() else Provider.NONE
    if configured == "xai":
        return Provider.XAI if settings.XAI_API_KEY.strip() else Provider.NONE

    # auto: whichever key is present.
    if settings.XAI_API_KEY.strip():
        return Provider.XAI
    if settings.ANTHROPIC_API_KEY.strip():
        return Provider.ANTHROPIC
    return Provider.NONE


def resolve_model(provider: Provider | None = None) -> str:
    provider = provider or resolve_provider()
    configured = (settings.LLM_MODEL or "").strip()
    return configured or DEFAULT_MODELS.get(provider, "")


def is_available() -> bool:
    return resolve_provider() is not Provider.NONE


def describe() -> dict[str, Any]:
    """Diagnostic summary. Never includes the key itself."""
    provider = resolve_provider()
    return {
        "configured": settings.LLM_PROVIDER,
        "resolved_provider": str(provider),
        "model": resolve_model(provider),
        "available": provider is not Provider.NONE,
        "timeout_seconds": settings.LLM_TIMEOUT_SECONDS,
        "anthropic_key_present": bool(settings.ANTHROPIC_API_KEY.strip()),
        "xai_key_present": bool(settings.XAI_API_KEY.strip()),
    }


# --- clients -------------------------------------------------------------------------


def _anthropic_client() -> Any:
    from anthropic import AsyncAnthropic

    return AsyncAnthropic(
        api_key=settings.ANTHROPIC_API_KEY, timeout=settings.LLM_TIMEOUT_SECONDS
    )


def _xai_client() -> Any:
    """xAI speaks the OpenAI wire format, so the openai SDK is the client."""
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=settings.XAI_API_KEY,
        base_url=settings.XAI_BASE_URL,
        timeout=settings.LLM_TIMEOUT_SECONDS,
    )


# --- operations ----------------------------------------------------------------------


async def complete_text(system: str, user: str, max_tokens: int = 400) -> str | None:
    """Free-text completion. Returns None if unavailable or anything goes wrong."""
    provider = resolve_provider()
    if provider is Provider.NONE:
        return None
    model = resolve_model(provider)

    try:
        if provider is Provider.ANTHROPIC:
            response = await _anthropic_client().messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return "".join(
                block.text
                for block in response.content
                if getattr(block, "type", None) == "text"
            ).strip() or None

        response = await _xai_client().chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return (response.choices[0].message.content or "").strip() or None

    except Exception as exc:  # noqa: BLE001 - the model is optional, never fatal
        logger.warning("LLM text completion failed (%s/%s): %s", provider, model, exc)
        return None


async def complete_tool(
    system: str, user: str, tool: ToolSpec, max_tokens: int = 1024
) -> dict[str, Any] | None:
    """Force a structured tool call and return its arguments, or None."""
    provider = resolve_provider()
    if provider is Provider.NONE:
        return None
    model = resolve_model(provider)

    try:
        if provider is Provider.ANTHROPIC:
            response = await _anthropic_client().messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                tools=[tool.as_anthropic()],
                tool_choice={"type": "tool", "name": tool.name},
                messages=[{"role": "user", "content": user}],
            )
            for block in response.content:
                if getattr(block, "type", None) == "tool_use":
                    return dict(block.input)
            return None

        response = await _xai_client().chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            tools=[tool.as_openai()],
            tool_choice={"type": "function", "function": {"name": tool.name}},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        calls = response.choices[0].message.tool_calls or []
        if not calls:
            return None
        import json

        return json.loads(calls[0].function.arguments)

    except Exception as exc:  # noqa: BLE001 - the model is optional, never fatal
        logger.warning("LLM tool completion failed (%s/%s): %s", provider, model, exc)
        return None
