"""Diagnose the language model configuration by actually calling it.

    docker compose exec api python /scripts/check_llm.py

Reports which provider resolved, which model id will be used, and whether a real text
call and a real tool call succeed. Model names change between provider releases, so a
wrong `LLM_MODEL` is the most likely failure — and because every LLM failure falls back
silently to the deterministic path by design, a broken key looks exactly like no key
from the outside. This is the tool that tells them apart.

Exit code 0 means the configuration works or is deliberately disabled; 1 means a
provider is configured but not usable.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for candidate in (REPO_ROOT / "apps" / "api", Path("/app")):
    if (candidate / "app" / "core" / "config.py").is_file():
        sys.path.insert(0, str(candidate))
        break

from app.services import llm  # noqa: E402

PROBE_TOOL = llm.ToolSpec(
    name="record_probe",
    description="Record a single test field so tool calling can be verified.",
    parameters={
        "type": "object",
        "properties": {
            "sector": {"type": "string", "enum": ["TRADE", "EDUCATION", "OTHER"]}
        },
        "required": ["sector"],
    },
)


def _warn_on_model_mismatch(info: dict) -> None:
    provider, model = info["resolved_provider"], (info["model"] or "")
    looks_anthropic = model.startswith("claude")
    looks_xai = model.startswith("grok")
    if provider == "xai" and looks_anthropic:
        print(f"  ! LLM_MODEL={model!r} looks like an Anthropic model but the provider "
              "is xai. Blank LLM_MODEL to use the provider default.")
    if provider == "anthropic" and looks_xai:
        print(f"  ! LLM_MODEL={model!r} looks like an xAI model but the provider is "
              "anthropic. Blank LLM_MODEL to use the provider default.")


async def main() -> int:
    info = llm.describe()

    print("SETU language model check")
    print("-" * 52)
    for label, key in (
        ("LLM_PROVIDER setting", "configured"),
        ("resolved provider", "resolved_provider"),
        ("model", "model"),
        ("timeout (s)", "timeout_seconds"),
        ("anthropic key present", "anthropic_key_present"),
        ("xai key present", "xai_key_present"),
    ):
        print(f"  {label:24s}: {info[key]}")
    _warn_on_model_mismatch(info)
    print()

    if not info["available"]:
        print("No provider configured. This is a supported configuration:")
        print("  - extraction uses the deterministic parser (app/services/numerals.py)")
        print("  - explanations use templates")
        print("  - eligibility is unaffected either way; the engine never used a model")
        print()
        print("To enable one, set XAI_API_KEY or ANTHROPIC_API_KEY in .env and restart.")
        return 0

    ok = True

    print("1. text completion ...", end=" ", flush=True)
    text = await llm.complete_text(
        system="You are a test probe. Reply with exactly the word: READY",
        user="Reply with the single word READY.",
        max_tokens=16,
    )
    if text:
        print(f"OK  -> {text[:60]!r}")
    else:
        print("FAILED (see API logs for the provider error)")
        ok = False

    print("2. tool calling  ...", end=" ", flush=True)
    payload = await llm.complete_tool(
        system="Extract the sector the user describes.",
        user="I run a small vegetable stall in the market.",
        tool=PROBE_TOOL,
        max_tokens=256,
    )
    if payload:
        print(f"OK  -> {payload}")
    else:
        print("FAILED — extraction will fall back to the deterministic parser")
        ok = False

    print()
    if ok:
        print("Provider is usable. Extraction may now enrich the deterministic pass,")
        print("and explanations will be model-written rather than templated.")
        print("Eligibility verdicts are unchanged: the engine never calls a model.")
    else:
        print("Provider is configured but not usable. The service still works — every")
        print("failure falls back to the deterministic path — but the LLM adds nothing.")
        print("Most likely cause: a wrong LLM_MODEL for this provider, or a bad key.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
