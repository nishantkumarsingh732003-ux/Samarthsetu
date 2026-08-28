# Project: SETU — Scheme Eligibility & Transparent Uptake

## What we are building
A multilingual, low-literacy-friendly platform for Smart India Hackathon 2026,
Problem Statement 26092 (Ministry of Social Justice & Empowerment).

A Scheduled Caste entrepreneur or student cannot easily answer two questions:
1. "Which government credit scheme actually fits me?"
2. "Which of the 100+ Channel Partners near me is authorised to process THAT scheme?"

Today they guess, walk into the wrong branch, and their application is misrouted or
delayed. We eliminate the guessing with a deterministic eligibility engine, a
geo-aware partner routing engine, and a conversational multilingual front door.

## Ground truth from the problem statement (do not contradict these)
- Beneficiary income ceiling: annual family income up to Rs 5,00,000
- Funding: up to 90% of project or education cost
- Concessional interest: typically 6.5% - 8% per annum
- NO direct loan applications. All funds route through a "Channel Finance System"
  of 100+ Channel Partners: State Channelising Agencies (SCA), Public Sector Banks (PSB),
  Regional Rural Banks (RRB), and NBFC-MFIs.
- Three scheme families to distinguish between:
  - Micro Finance Scheme  — small projects, up to Rs 1,40,000
  - Term Loan             — larger projects, up to Rs 50,00,000
  - Educational Loan Scheme
- Core pain: confusion between schemes + inability to locate the nearest partner
  authorised for that specific loan category.

## Non-negotiable engineering rules
1. **Eligibility is NEVER decided by an LLM.** A deterministic, versioned rule engine
   decides. The LLM only (a) extracts structured facts from messy user input and
   (b) explains the rule engine's output in the user's language. Every eligibility
   response must be reproducible and traceable to a rule ID.
2. **Every scheme rule carries provenance**: `source_url`, `circular_ref`,
   `effective_from`, `last_verified_on`. Never hardcode a number without a source field.
3. **Explainability is a feature, not a nicety.** Every match returns
   `matched_because[]` and `blocked_because[]` with human-readable reasons.
4. **Privacy by default (DPDP Act 2023).** Aadhaar and any government ID is masked at
   ingestion — store only last 4 digits plus a salted hash. Explicit consent record
   before any data is stored. Full audit log of who read what.
5. **Assume 2G and a Rs 6,000 phone.** Offline-first PWA, budget < 200KB JS on the
   citizen route, works without JS for the core flow where possible.
6. **No mock data in the demo path.** Seed realistic data via scripts so every screen
   is populated from the real database.

## Tech stack (fixed — do not substitute)
- Monorepo, pnpm workspaces
- `apps/web`      — Next.js 14 App Router, TypeScript, Tailwind, shadcn/ui, next-intl
- `apps/api`      — FastAPI (Python 3.11), SQLAlchemy 2.0, Alembic, Pydantic v2
- `packages/rules`— TypeScript + Python-readable YAML scheme rule definitions (shared)
- Database        — PostgreSQL 16 with PostGIS (partner geo) and pgvector (semantic search)
- Cache/queue     — Redis
- Everything runs via `docker compose up`

## Language support (priority order)
English, Hindi, Marathi, Bengali, Tamil, Telugu. Use next-intl with ICU messages.
Never machine-translate legal scheme names — keep official names verbatim with a
transliterated gloss.

## Definition of done for any phase
- `docker compose up` works from a clean clone
- `pnpm test` and `pytest` pass
- No TODO/FIXME left in committed code
- README updated with how to run what you just built
