# Architecture

## Layers

```
┌──────────────────────────────────────────────────────────────┐
│  apps/web  Next.js 14 · 6 languages · voice-first · PWA      │
└───────────────────────────┬──────────────────────────────────┘
                            │ REST /api/v1
┌───────────────────────────▼──────────────────────────────────┐
│  apps/api  FastAPI                                            │
│   routes: match · partners · conversation · applications ·    │
│           documents · partner console · admin                 │
│   services: orchestration, caching, audit                     │
└───────────┬───────────────────────────────┬──────────────────┘
            │                               │
┌───────────▼──────────────┐   ┌────────────▼──────────────────┐
│  packages/rules          │   │  PostgreSQL 16                 │
│  1 eligibility (rules)   │   │   + PostGIS  (partner geo)     │
│  2 ranking (fit score)   │   │   + pgvector (scheme search)   │
│  3 explain (LLM)         │   │  schemes · partners · profiles │
│  next_best_question()    │   │  applications · match_runs     │
└──────────────────────────┘   │  audit_log                     │
                               └────────────────────────────────┘
                               ┌────────────────────────────────┐
                               │  Redis (session, cache, jobs)  │
                               └────────────────────────────────┘
```

## Matching pipeline

1. **Extract** — messy speech or text → canonical fields (income, category, state,
   purpose, amount, age). Indian numeral forms ("ढाई लाख", "2.5 lakh") are parsed by a
   deterministic parser, never by the LLM. Low-confidence fields become confirmation
   questions instead of silently entering the profile.
2. **Eligibility** — deterministic, versioned rules in `packages/rules/schemes/`. Every
   rejection is recorded with a rule ID so the UI can say *why not*. A hard-block rule
   that references a null field yields `NEED_MORE_INFO`, not a guess.
3. **Ask** — `next_best_question()` returns the single field that removes the most
   ambiguity, so the questionnaire only asks what can change the outcome.
4. **Rank** — pure function over fit-to-project-cost, interest rate, and funding
   percentage.
5. **Explain** — the LLM restates the rule trace in plain language in the user's
   language. It may not add, infer, or soften any conclusion.
6. **Route** — PostGIS distance query for the nearest partners, **hard-filtered by the
   scheme they are authorised to process** and their ticket-size band, with a `why_not`
   list for nearby partners that were excluded.

## Key design decisions

- Eligibility is **rules, never LLM** — it is a legal determination and must be auditable.
- The LLM only explains and translates; it can never grant or deny eligibility.
- Scheme + partner catalogues are versioned data, not code, so policy changes are a data
  edit: change the YAML, bump `engine_version`, re-run the golden tests.
- Every match writes a `match_runs` row (input snapshot, engine version, results) — the
  admin console can replay any decision.
- Every scheme rule carries `source_url`, `circular_ref`, `effective_from`, and
  `last_verified_on`. Figures the problem statement does not state are marked
  `needs_verification: true` rather than invented.

See `docs/adr/` for individual decision records and `docs/reference/` for pre-Phase-1
material that is explicitly **not** authoritative.
