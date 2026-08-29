"""Test isolation.

The suite must never reach the network. Without this, a developer who has
`GROQ_API_KEY` (or any provider key) exported in their shell gets a completely
different test run from CI: extraction and explanation start making real model calls,
four tests fail, and the suite takes seven minutes instead of one second.

Provider settings are therefore neutralised for every test. A test that wants to
exercise a configured provider opts back in explicitly via the `env` fixture in
test_llm.py, which monkeypatches the same settings.
"""

from __future__ import annotations

import pytest

from app.core.config import settings


@pytest.fixture(autouse=True)
def no_live_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force the language model off, whatever the developer's environment says."""
    monkeypatch.setattr(settings, "LLM_PROVIDER", "none")
    monkeypatch.setattr(settings, "ANTHROPIC_API_KEY", "")
    monkeypatch.setattr(settings, "XAI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
