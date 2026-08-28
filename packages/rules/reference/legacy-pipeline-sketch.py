"""End-to-end matching pipeline.

profile -> eligibility filter -> retrieval -> ranking -> explanation -> partner routing

Eligibility is deterministic and auditable (see docs/adr/0001). The LLM only explains.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MatchTrace:
    """Everything needed to replay and justify a decision."""

    rule_pack_version: str = ""
    evaluated: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)


def run(profile: dict[str, Any]) -> tuple[list[dict[str, Any]], MatchTrace]:
    """Return ranked scheme matches and the trace that produced them."""
    raise NotImplementedError
