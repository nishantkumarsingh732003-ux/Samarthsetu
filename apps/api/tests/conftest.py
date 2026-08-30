"""Test isolation.

The suite must never reach a language model, regardless of what happens to be in the
developer's environment. Without this, a machine with GROQ_API_KEY exported runs the
extraction and explanation tests against a live provider: slow, flaky, billable, and
quietly testing something other than what the test claims to test.

This was not hypothetical — a real run took 407 seconds and produced four failures for
exactly that reason.

A test that genuinely wants a provider configured sets it explicitly through the `env`
fixture in test_llm.py, which monkeypatches the same settings after this has run.
"""

from __future__ import annotations

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def no_live_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable every provider for the duration of each test."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "XAI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    monkeypatch.setattr(settings, "LLM_MODEL", "")
