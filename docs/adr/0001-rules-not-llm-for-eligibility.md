# ADR 0001: Rules-based eligibility, LLM-based explanation only

**Status:** Accepted

## Context
Eligibility for concessional credit is a legal determination governed by published
criteria (income ceiling, caste certificate, age, purpose, state of residence).

## Decision
Eligibility is computed by deterministic, versioned rules. The LLM is used only to
explain a decision and to translate it. The LLM can never flip an eligibility verdict.

## Consequences
- Every verdict is reproducible and auditable.
- Policy changes are data/rule edits, reviewable by domain officers.
- Explanation quality depends on the rule trace being rich enough to narrate.
