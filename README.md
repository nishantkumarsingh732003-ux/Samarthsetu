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

That is the whole setup — verified at 39 seconds from destroyed volumes to a healthy
stack. It builds a Postgres 16 image with **PostGIS and pgvector**,
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

## API

Three endpoints as of Phase 2. Interactive docs at http://localhost:8000/docs.

### `POST /api/v1/match` — which schemes fit

Runs the deterministic rule engine. Writes a `match_runs` row and an `audit_log` entry
before returning, so the verdict can be replayed later.

```bash
curl -s -X POST http://localhost:8000/api/v1/match   -H 'Content-Type: application/json'   -d '{
    "profile": {
      "category": "SC",
      "project_sector": "TRADE",
      "annual_family_income": 180000,
      "project_cost": 80000
    },
    "language": "en"
  }'
```

A partial profile is not a refusal — it returns `NEED_MORE_INFO` plus the single next
question worth asking:

```bash
curl -s -X POST http://localhost:8000/api/v1/match   -H 'Content-Type: application/json' -d '{"profile": {}}'
# -> every scheme NEED_MORE_INFO, next_question.field = "category"
```

An unknown profile field is rejected with `422` naming the field, rather than silently
ignored.

### `POST /api/v1/partners/route` — who can actually process it

```bash
curl -s -X POST http://localhost:8000/api/v1/partners/route   -H 'Content-Type: application/json'   -d '{
    "scheme_code": "NSFDC_MICRO_FINANCE",
    "amount": 90000,
    "lat": 21.1458,
    "lng": 79.0882,
    "district": "Nagpur"
  }'
```

`lat`/`lng` may be omitted if `district` is given; the origin is then derived from the
partners already on record there. Results are cached in Redis for 10 minutes on
`(scheme, amount band, geohash-5 cell)`, and the response carries `"cached": true` when
served from it.

Abridged output for that request — 60 nearest partners considered, 5 eligible:

```
#1  Fusion Micro Finance — Nagpur Service Centre
    NBFC_MFI | 9.51 km | 31d turnaround | 14% load | SCORE 0.745
    distance=0.3239  turnaround=0.0921  type_affinity=0.2  load=0.129
#2  Vidharbha Konkan Gramin Bank, Nagpur Branch
    RRB | 4.85 km | 38d turnaround | 13% load | SCORE 0.7078
#3  Mahatma Phule Backward Class Development Corporation — Nagpur District Office
    SCA | 3.91 km | 30d turnaround | 90% load | SCORE 0.6224

WHY NOT:
  [NOT_ACCEPTING]  Maharashtra Gramin Bank, Nagpur Branch is 8.32 km away but has
                   paused new Micro Finance Scheme applications because its capacity
                   is exhausted.
  [NOT_AUTHORISED] UCO Bank, Jabalpur Main Branch is 242.27 km away but is not
                   authorised for the Micro Finance Scheme.
  [TOO_FAR]        CreditAccess Grameen — Jabalpur Service Centre is authorised for
                   the Micro Finance Scheme but is 248.83 km away, beyond the 150 km
                   service radius.
```

The nearest branch is not the answer. Note that #1 sits 9.5km away and outranks a
branch at 3.9km, because that closer branch is 90% loaded — and every component of
that judgement is returned separately in `score_breakdown` rather than hidden inside
one number.

`why_not` is the anti-misrouting feature. Rejection reason codes:

| Code | Meaning |
|---|---|
| `NOT_AUTHORISED` | No authorisation row for this scheme — the branch cannot take it at all |
| `NOT_ACCEPTING` | Authorised, but capacity is exhausted right now |
| `BELOW_MIN_TICKET` / `ABOVE_MAX_TICKET` | Amount outside the branch's ticket band |
| `TOO_FAR` | Authorised but beyond the 150km service radius |
| `DISTRICT_NOT_SERVED` | Does not serve the citizen's district for this scheme |

### `GET /api/v1/partners/{id}` — one partner and its full authorisation matrix

```bash
curl -s http://localhost:8000/api/v1/partners/<uuid>
```

Returns the branch plus every scheme it is authorised for, with ticket bands, capacity,
turnaround and service districts.

### `POST /api/v1/conversation/turn` — the conversational front door

Extracts facts from the citizen's own words, merges them into a Redis-backed session,
and runs the deterministic engine. Omit `session_id` to start; the reply returns one.

```bash
curl -s -X POST http://localhost:8000/api/v1/conversation/turn   -H 'Content-Type: application/json'   --data-binary '{"utterance": "mujhe assi hazaar chahiye", "language": "hi"}'
```

A four-turn Hindi conversation, abridged:

```
turn 1  "नमस्ते, मैं सब्जी बेचती हूँ"     -> project_sector=TRADE (0.88)
        ask: आपको कुल कितने पैसे की ज़रूरत है?
turn 2  "मैं अनुसूचित जाति से हूँ"          -> category=SC (0.95)
turn 3  "मेरी सालाना आय ढाई लाख है"        -> annual_family_income=250000 (0.95)
turn 4  "मुझे अस्सी हजार चाहिए"            -> project_cost=80000 (0.95)
        DECIDED (3 of at most 6 questions)
          1. NSFDC_MICRO_FINANCE   ELIGIBLE     Rs 72,000
          2. NSFDC_TERM_LOAN       INELIGIBLE
          3. NSFDC_EDUCATION_LOAN  INELIGIBLE
        explanation: आप Micro Finance Scheme के लिए पात्र हैं...
        rule ids: MF_CATEGORY_SC, MF_INCOME_CEILING, MF_NOT_FOR_EDUCATION, ...
```

**Where the language model sits.** Extraction runs strictly *before* the engine and
only proposes candidate facts. Explanation runs strictly *after* it and may only
restate its reasons. Nothing a model emits reaches a verdict — proved by
`test_hindi_conversation_matches_the_direct_engine_call`, which asserts that the
profile reached by conversation and the same profile passed straight to the engine
produce byte-identical results.

**Amounts are never the model's job.** `app/services/numerals.py` parses `2,50,000`,
`2.5 lakh`, `dhai lakh`, `ढाई लाख`, `२,५०,०००`, `২,৫০,০০০` and `do lakh chalees hazaar`
to the same 250000, with 59 tests. The extraction tool schema does not even offer the
model a money field.

**Uncertainty becomes a question, not a guess.** A reading below 0.7 confidence is not
written. A bare "ढाई लाख" with no context returns
*"मैंने समझा कि आपकी सालाना पारिवारिक आय लगभग Rs 250,000 है — क्या यह सही है?"*

**The model provider is pluggable, and "none" is a supported setting.** Set
`LLM_PROVIDER=auto|anthropic|xai|groq|none` in `.env`; `auto` uses whichever key is
present.

| Provider | Key looks like | Serves | Endpoint |
|---|---|---|---|
| `anthropic` | `sk-ant-…` | Claude | Anthropic SDK |
| `xai` | `xai-…` | **Grok** (xAI's own models) | `api.x.ai/v1` |
| `groq` | `gsk_…` | **Groq** — open models (Qwen, gpt-oss…) on custom inference hardware | `api.groq.com/openai/v1` |

Verified live on Groq with `qwen/qwen3.8-27b` (2026-08-29): a Hindi conversation with
the model in the loop produced **byte-identical verdicts** to calling the engine
directly. Note that `groq/compound-mini` has no tool calling and `openai/gpt-oss-*` are
reasoning models that need generous `max_tokens` before they emit any content.

Grok and Groq are different companies with near-identical names; both are named
explicitly so a key cannot be silently used against the wrong one. xAI and Groq are both
OpenAI wire-compatible, so they share a client path and one neutral `ToolSpec` renders
to both Anthropic tool-use and OpenAI function-calling shapes.

With no key at all, the model passes are skipped, deterministic extraction carries the
conversation and explanations come from templates.

Because every LLM failure falls back silently by design, a broken key looks exactly like
no key from outside. This tells them apart:

```bash
docker compose exec api python /scripts/check_llm.py
```

It reports the resolved provider and model, warns on a provider/model mismatch, then
makes a real text call and a real tool call.

**All six languages, honestly labelled.** English, Hindi, Marathi, Bengali, Tamil and
Telugu have complete rule messages, question text, explanation templates and extraction
cues. English and Hindi are **verified**; the other four are **draft** — machine-written
and not yet read by a native speaker. Every `MatchResult` carries `translation_status`
so a UI can badge unreviewed copy. Adding or promoting a language is one file: see
[packages/rules/translations/](packages/rules/translations/README.md).

**Sessions hold no PII.** Redis, 24h TTL, storing the eligibility profile and which
fields each turn established — never the citizen's raw words, which routinely contain a
name, a village or a number spoken aloud.


### Routing weights

All in [apps/api/app/core/routing_config.py](apps/api/app/core/routing_config.py) —
distance 0.40, turnaround 0.25, type affinity 0.20, load 0.15. They are returned in
every routing response so the ranking can be argued with rather than reverse-engineered.


## Vendored skills

`.claude/skills/` contains 376 skills vendored from
[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)
(MIT). `.claude/skills-manifest.json` records the upstream commit and the source path
of every skill. These are development aids for the team — they are not part of the
deployed application.

## Status

Phases 0 (foundation), 1 (eligibility engine), 2 (partner registry and geo routing) and
3 (conversational intake) are complete. See [CLAUDE.md](CLAUDE.md)
for the engineering contract every phase must satisfy.

```bash
pytest packages/rules -q          # 97 tests — the eligibility engine
pnpm --filter @setu/rules test    # 19 tests — TypeScript conformance with Python
cd apps/api && pytest -q          # 113 tests — schema, routing, numerals, conversation
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
