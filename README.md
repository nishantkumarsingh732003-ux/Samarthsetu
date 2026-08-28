# SETU — Scheme Eligibility & Transparent Uptake

**SIH 2026 — Problem Statement 26092: AI-Driven Scheme Matching for Marginalized Entrepreneurs**

| | |
|---|---|
| Organization | Ministry of Social Justice and Empowerment (MoSJE) |
| Department | Department of Social Justice and Empowerment |
| Category | Software |
| Theme | Smart Automation |

## The problem

SC-community citizens with family income up to ₹5.00 lakh are eligible for concessional
credit (6.5%–8% p.a., up to 90% of project cost), but:

1. They don't know **which** scheme fits them — Micro Finance (≤ ₹1.40 L),
   Term Loan (≤ ₹50.00 L), or Educational Loan.
2. Direct applications are not accepted. Funds route through a **Channel Finance System**
   of 100+ partners (SCAs, PSBs, RRBs, NBFC-MFIs) and applicants can't find the nearest
   authorized partner that handles their loan category.

## The solution

A deterministic eligibility engine, a geo-aware partner routing engine, and a
conversational multilingual front door.

```
Citizen profile ──▶ Eligibility rules ──▶ Ranking ──▶ Explained match
   (voice/text,        (versioned,        (fit score)     + nearest AUTHORISED
    6 languages)        auditable)                          Channel Partner
```

**The LLM never decides eligibility.** A versioned rule engine decides; the LLM only
extracts facts from messy input and restates the engine's reasons in the user's
language. Every verdict is reproducible and traceable to a rule ID. See
[docs/adr/0001-rules-not-llm-for-eligibility.md](docs/adr/0001-rules-not-llm-for-eligibility.md).

## Repository layout

| Path | What lives here |
|---|---|
| `apps/api/` | FastAPI service — matching API, partner routing, applications, audit |
| `apps/web/` | Next.js citizen app (multilingual, low-literacy friendly, offline-first) |
| [`packages/rules/`](packages/rules/README.md) | Versioned YAML scheme rules + the deterministic eligibility engine (Python + TypeScript) |
| `infra/` | Docker, Kubernetes, nginx, Terraform |
| `docs/` | [Architecture](docs/architecture.md), [data model](docs/data-model.md), [open items](docs/OPEN_ITEMS.md), API spec, ADRs |
| `scripts/` | Setup and seed scripts |
| `.claude/skills/` | Vendored skill library (see below) |

## Running locally

Requires Docker, Node 20+ with pnpm, and Python 3.11.

```bash
cp .env.example .env
docker compose up
```

That is the whole setup. It builds a Postgres 16 image with **PostGIS and pgvector**,
creates both extensions on first start (`scripts/seed/00_extensions.sql`), waits for the
database, applies `alembic upgrade head`, and serves the API and web app.

| | |
|---|---|
| Web | http://localhost:3000 |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

Load reference and demo data (safe to re-run — every seeder is idempotent):

```bash
make seed                    # or: python scripts/seed/run.py --list
```

To run the services directly instead of in Docker:

```bash
./scripts/setup.sh           # install API and web dependencies
make migrate                 # alembic upgrade head
make api                     # uvicorn on :8000
make web                     # next dev on :3000
```

### Working on the schema

```bash
cd apps/api
alembic revision --autogenerate -m "what changed"   # needs a running database
alembic upgrade head --sql                          # render DDL without a database
pytest -q                                           # schema tests, no database needed
```

The schema tests assert the things that must not regress: the PostGIS and GIN indexes
the routing engine depends on, the four-digit CHECK constraints that make a full
Aadhaar number unstorable, the provenance columns on `schemes`, and that Alembic has a
single head.

## Vendored skills

`.claude/skills/` contains 376 skills vendored from
[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)
(MIT). `.claude/skills-manifest.json` records the upstream commit and the source path
of every skill. These are development aids for the team — they are not part of the
deployed application.

## Status

Phases 0 (foundation) and 1 (eligibility engine) are complete. See [CLAUDE.md](CLAUDE.md)
for the engineering contract every phase must satisfy.

```bash
pytest packages/rules -q          # 97 tests — the eligibility engine
pnpm --filter @setu/rules test    # 19 tests — TypeScript conformance with Python
cd apps/api && pytest -q          # 10 tests — schema guarantees
```

Known gaps and blockers are tracked in [docs/OPEN_ITEMS.md](docs/OPEN_ITEMS.md).

## Data disclaimer

Channel Partner records used in the demo are **synthetic**, pending the official MoSJE
partner master.

Scheme figures in `packages/rules/schemes/` are verified against
[nsfdc.nic.in](https://nsfdc.nic.in/scheme) as of 2026-08-29, but no scheme **circular
number** has been located, so all three carry `needs_verification: true` with
`circular_ref` and `effective_from` null rather than guessed. Figures with no single
sourced value stay null and are recorded as open questions. See
[packages/rules/README.md](packages/rules/README.md#provenance-status--read-before-quoting-any-number)
and [docs/OPEN_ITEMS.md](docs/OPEN_ITEMS.md).
