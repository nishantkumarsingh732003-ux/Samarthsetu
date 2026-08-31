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
| Citizen app | http://localhost:3000 |
| Staff console | http://localhost:3000/console/login |
| Feature-phone demo | http://localhost:3000/demo/whatsapp |
| API docs | http://localhost:8000/docs |
| Health | http://localhost:8000/health |

Load reference and demo data (safe to re-run — every seeder is idempotent):

```bash
make seed                    # or: python scripts/seed/run.py --list
```

That also creates the three console logins. They are demo credentials with a published
password, which is deliberate for a synthetic-data build — set `SEED_PASSWORD` to change
them, and the seeder **refuses to run at all** with the default password unless
`ENVIRONMENT=development`:

| Role | Email | Lands on |
|---|---|---|
| Ministry analyst | `admin@setu.gov.in` | `/console/admin` |
| Branch officer | `partner@setu.gov.in` | `/console/partner` |
| Citizen | `citizen@setu.gov.in` | nothing — the citizen service needs no account |

Password: `setu-demo-2026`

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


### `POST /api/v1/applications` — submit to a Channel Partner

Consent is written **before** the citizen row, and `citizens.consent_id` is NOT NULL, so
there is no code path that stores personal data without a consent record to point at.
Every applicant field is optional except the consent grant; a citizen who will not type
their Aadhaar into a phone still gets a reference number and a branch to walk into.

```bash
curl -s localhost:8000/api/v1/applications -H 'Content-Type: application/json' -d '{
  "scheme_code": "NSFDC_MICRO_FINANCE",
  "partner_id": "<from /partners/route>",
  "amount_requested": 72000,
  "match_run_id": "<from /match>",
  "applicant": {"display_name": "Sunita Devi", "gov_id_type": "AADHAAR",
                "gov_id": "2345 6789 0123", "state": "Maharashtra"},
  "consent": {"granted": true},
  "language": "hi"
}'
# -> {"reference_no": "SETU-2026-MH-000001", "status": "SUBMITTED",
#     "engine_version": "2.2.0", "documents_outstanding": 7, ...}
```

The reference number is designed to be read aloud at a branch counter over a bad line:
`SETU-<year>-<state>-<serial>`. Withholding consent returns **403** and writes nothing —
not a consent row, not a citizen row.

The application snapshots `match_run_id` and the `engine_version` **that run recorded**,
not whatever is live now. A sanction six months later can be replayed against the rules
that were actually in force when the citizen applied.

### `POST /api/v1/applications/{ref}/documents` — upload, redacted before it is stored

OCR runs locally via tesseract in the API image. An Aadhaar card is not uploaded to a
third-party API to find out what it says.

```
IDENTITY_PROOF
  redaction applied : True
  kept about the ID : [{"id_type": "AADHAAR", "last4": "0123", "salted_hash": "92d1711710..."}]
  text we stored    : 'Governmentofindia Sunita Devi 1406/1988 XXXX XXXX 0123'

INCOME_CERTIFICATE
  status  : WARNING
  warning : [POSSIBLY_EXPIRED] This appears to be dated 2019. Most partners require one
            issued within the last 6 months.
```

**Warnings never block.** Telling a citizen their income certificate looks four years old
while they are still at home saves them a trip; refusing the upload over it moves the
failure somewhere they cannot see. The citizen decides.

**Redaction fails closed.** If OCR is unavailable, an ID-bearing document is refused with
**503** rather than stored unredacted. If an ID is found in the text but cannot be located
in the pixels, the upload is refused too — storing it would leak it. Losing an upload is
recoverable; leaking an Aadhaar number is not.

### `GET /api/v1/applications/{ref}` — the tracking view

No login. A citizen who walked to a cyber cafe with a number on a slip of paper must be
able to check their application, so the response carries the state of the application and
no personal data at all. A 404 is worded identically whether the reference never existed
or belongs to someone else, so it cannot be used as an oracle.

### `POST /api/v1/applications/{ref}/transition` — partner-side status

Illegal transitions are refused with **409** and a message naming what *is* allowed:

```
SUBMITTED cannot become SANCTIONED.
Allowed from here: PARTNER_ACKNOWLEDGED, REJECTED, WITHDRAWN.
```

A partner cannot sanction an application it never acknowledged. The transition table is a
model of the process, not a log of whatever happened.

### `GET /api/v1/documents/checklist` — what to actually bring

Narrowed by scheme family, partner type and the facts already given, with a stated reason
for each document. A condition that cannot yet be decided **includes** the document:
over-listing costs a citizen one extra sheet of paper, under-listing costs them a second
trip to the branch, which is the failure this project exists to prevent.

Sunita gets 7 documents, Ramesh 10, Anjali 10 — the same engine, different lists.


### Routing weights

All in [apps/api/app/core/routing_config.py](apps/api/app/core/routing_config.py) —
distance 0.40, turnaround 0.25, type affinity 0.20, load 0.15. They are returned in
every routing response so the ranking can be argued with rather than reverse-engineered.


## The citizen app

Designed for a 5-inch screen, one hand, bright sunlight, and someone who may not read
fluently.

| Route | What it is |
|---|---|
| `/` | Language picker — six large targets, native script, no locale guessed |
| `/[locale]` | One primary action, named rather than "Start" |
| `/[locale]/assist` | Voice or typed conversation; answers shown as chips to correct |
| `/[locale]/results` | Ranked scheme cards, ineligible ones shown greyed with the blocking reason |
| `/[locale]/results/[scheme]/partners` | Map + list, score-breakdown bars, "nearby but cannot help" |
| `/[locale]/apply/[scheme]` | Consent, optional applicant details, and the document checklist before you submit |
| `/[locale]/track/[ref]` | Status timeline plus document upload — no login, the reference number is the key |
| `/console/login` | One sign-in form; the role in the response decides where you land |
| `/console/partner` | Branch officer's queue, capacity toggle, SLA clock |
| `/console/admin` | Ministry dashboard — funnel, misrouting KPI, underserved districts |
| `/demo/whatsapp` | Feature-phone simulator — same orchestrator, plain text, segment costs |

```bash
pnpm --filter @setu/web dev     # http://localhost:3000
pnpm --filter @setu/web check   # i18n + contrast + build + bundle budget
```

### Lighthouse, production build

| | /en | /hi | /ta |
|---|---|---|---|
| Performance | **100** | **100** | **100** |
| Accessibility | **100** | **100** | **100** |
| Best Practices | **100** | **100** | **100** |
| SEO | **100** | **100** | **100** |

FCP 0.8s · LCP 1.8s · TBT 0ms · CLS 0, under Lighthouse's mobile throttling.

### The budget is enforced, not hoped for

Worst citizen route is **114.4 KB gzipped of a 200 KB budget**. `check-bundle.mjs` reads
the real build manifest and fails the build if a route crosses the line. Leaflet is ~150KB,
so the map is behind a dynamic import — a citizen who never opens it never downloads it.

### Three checks that fail the build

- **`check:i18n`** — key parity across all six catalogues, review status declared, and a
  grep for hardcoded copy in components. A missing key does not crash next-intl; it
  silently renders the key name to a citizen, which is worse than a build failure.
- **`check:contrast`** — every foreground/background pair in the palette against WCAG AA,
  whether or not a page currently uses it. Lighthouse only sees the colours on the page
  it audited.
- **`check:bundle`** — the JS budget above.

### Offline

A hand-written service worker (no PWA plugin — it would spend the budget it is meant to
protect) with three rules: navigations network-first falling back to the cached shell,
static assets cache-first, and **the API never cached**. An eligibility verdict must not
be served stale. Results the citizen has already seen live in `localStorage`, so
`/results` renders with the network gone, under a persistent "Offline — showing saved
results" banner.


## The two consoles

Three roles, three genuinely different experiences, one sign-in form. Authorisation is a
`WHERE` clause, not a permission check: every partner-side query filters on the signed-in
user's `partner_id`, so a forgotten guard returns nothing rather than silently widening
the result set.

```
                    /partner/queue   /admin/analytics
  admin token           403               200
  partner token         200               403
  citizen token         403               403
  no token              401               401
```

### `/console/partner` — the branch officer

The queue answers "what should I pick up next?" without opening anything: document
readiness with the missing items **named**, an SLA clock against the partner's own stated
turnaround, and — one click away — why the router sent this application here, with the
rule IDs attached. An officer who can see why a case landed on their desk can push back
when it should not have.

The stored decision holds its reasons in the *citizen's* language. The console rebuilds
them in the officer's, from stable rule IDs:

```
[en] MF_CATEGORY_SC: You are a Scheduled Caste applicant.
[hi] MF_CATEGORY_SC: आप अनुसूचित जाति के आवेदक हैं।
[ta] MF_CATEGORY_SC: நீங்கள் பட்டியலின சாதி விண்ணப்பதாரர்.
```

**The capacity toggle is the live demo.** It writes to the same
`partner_scheme_authorisations` rows the routing engine hard-filters on, and invalidates
the routing cache, so pausing intake removes the branch from citizen routing on the very
next call — and tells anyone nearby exactly why:

```
1. Before  #1 Fusion Micro Finance — Nagpur Service Centre     <- offered
2. Officer sets Micro Finance Scheme: accepting = false
3. After   #1 Vidharbha Konkan Gramin Bank, Nagpur Branch      <- gone from the list
   why_not: "Fusion Micro Finance — Nagpur Service Centre is 9.51 km away but has
             paused new Micro Finance Scheme applications because its capacity is
             exhausted."
4. Officer resumes -> offered again
```

Rejecting or requesting documents **requires a reason**. Telling a citizen "no" without
saying why is the behaviour this project exists to replace.

### `/console/admin` — the ministry dashboard

Every figure is a query against the live database. No chart library, no fixture, no
cached snapshot; the bars are `div`s, so a screen reader gets the number rather than a
canvas it cannot describe.

**Misrouting prevented** is stated first, because it is the thing this service exists to
change. It is counted from `audit_log` rows the routing endpoint writes, broken down by
the rule that excluded each branch — "not authorised for this scheme" and "too far" are
different policy problems and are reported separately.

**Underserved districts** is the one section that tells the ministry to *do* something
rather than how they are doing: districts where citizens ran an eligibility check and no
authorised, accepting partner can process what they matched. Demand is measured from
eligibility checks rather than applications, because the citizens who matter most are the
ones who looked, found nothing, and never reached the application table at all.

```
District          Demand  Partners  Families unserved
Nagpur, MH             1         6  education loan
```

Every section exports to CSV (`utf-8-sig`, so Excel opens Devanagari and Tamil labels
rather than mojibake).

#### The acceptance test: adding one application moves every number

```
metric                 before    after   moved
eligibility runs           42       43   yes
matched                    18       19   yes
routed                     11       12   yes
applied                     1        2   yes
misrouting KPI            259      316   yes
routing calls              11       12   yes
districts w/demand          1        2   yes
scheme mix rows             1        2   yes
language rows               1        2   yes
status rows                 1        2   yes
turnaround rows             1        1   no   <- correct: still SUBMITTED
```

Turnaround only counts applications that have moved past submission. It moves on the
partner's next action, not on the citizen's — which is the honest reading of the metric,
so it is left that way.

### Auth, and what it deliberately is not

Email, password, a signed JWT, three roles. No OAuth provider, no email verification, no
refresh-token rotation. **Production integrates with NIC / Parichay SSO** and
`/api/v1/auth/login` is the seam where that swap happens — nothing else in the API asks
anything but "who is calling".

`bcrypt` is used directly rather than through `passlib`: passlib 1.7.4 raises
`ValueError: password cannot be longer than 72 bytes` on import against modern bcrypt.
A password over that limit is **refused, not truncated** — silent truncation means two
different passwords open one account. An unknown email is verified against a real dummy
hash so it costs the same ~200ms as a known one, because response timing is otherwise an
oracle for which addresses are registered.


## Reach: the citizens a smartphone app never gets to

The people furthest from a Channel Partner branch are also the least likely to own a
smartphone. A service that only reaches people who already have one has selected against
exactly the citizens it was funded to help.

### `POST /api/v1/webhook/whatsapp` — the same product, over text

This is not a second implementation. Every message runs `conversation.handle_turn`, the
identical function the citizen app calls: same deterministic rule engine, same six
languages, same rule IDs. Only the *rendering* is different, and that lives in the route
because it is a property of the channel.

Try it without a Meta account at **http://localhost:3000/demo/whatsapp**:

```
>> mujhe sabzi ka thela lagana hai
   आपको कुल कितने पैसे की ज़रूरत है?                     [ASKING · 1 segment]

>> 80 hazaar
   आप किस सामाजिक श्रेणी से हैं?
   1) SC   2) ST   3) OBC   4) GENERAL
   Reply with the number.                                [ASKING · 2 segments]

>> 1
   आपके परिवार की कुल वार्षिक आय कितनी है?               [ASKING · 1 segment]

>> 1.8 lakh
   *Micro Finance Scheme*
   - आप अनुसूचित जाति के आवेदक हैं।
   - आपकी वार्षिक पारिवारिक आय Rs 5,00,000 की सीमा के भीतर है।
   Indicative: up to Rs 72,000
   SETU does not lend. A Channel Partner decides.        [DECIDED · 4 segments]
```

A complete eligibility journey in four keypad messages. Meta's real webhook contract is
honoured — `GET` answers `hub.challenge`, `POST` parses their envelope and ignores
delivery receipts — and a WhatsApp sender is a phone number, so the session key is a
**salted hash of it**; the number is never written down.

### Notifications, and the arithmetic nobody costs

Every status change a citizen would want to know about renders a message in their own
language and stores it. Four drivers behind one interface; the demo runs on `database`,
which needs no contact address, no network and no third party.

```
event                  ch      lang  seg  body
APPLICATION_SUBMITTED  IN_APP  ta     3   SETU: விண்ணப்பம் SETU-2026-MH-000001 …க்கு அனுப்பப்பட்டது…
PARTNER_ACKNOWLEDGED   IN_APP  ta     2   SETU: … உங்கள் விண்ணப்பம் … பெற்று பரிசீலிக்கிறது.
DOCS_REQUESTED         IN_APP  ta     3   SETU: …க்கு ஆவணம் தேவை. Caste certificate is not readable. …
UNDER_APPRAISAL        IN_APP  ta     2   SETU: … இப்போது விண்ணப்பம் … ஆய்வு செய்கிறது.
SANCTIONED             IN_APP  ta     2   SETU: … அனுமதித்தது. அடுத்த படிகளை அவர்கள் தெரிவிப்பார்கள்.
```

**That `seg` column is the point.** An SMS segment is 160 characters in GSM-7 and **70 in
UCS-2** — and every Indic script forces UCS-2. A message that costs one segment in
English costs three in Tamil, and the sender pays per segment. `sms_segments()` implements
the real encoding rules (including that an emoji is two code units and `€` is two
septets), a test asserts no template exceeds two segments in any of the six languages, and
the count is stored on every row. The cost of serving people in their own language is
visible at the point the messages are written, not on an invoice later.

**The SMS and WhatsApp drivers refuse rather than pretend.** They implement the same
interface and are wired in, but Phase 5 stores only `phone_last4`, so there is nothing to
dial. They raise `ContactUnavailable`; a driver that returned `SENT` would put a green
tick beside a message nobody received. Lifting that is a schema and consent decision, not
something to slip in behind a notification feature — see OI-43.

## Hardening: what happens when things break

### `make chaos` — the drill

`scripts/chaos.sh` points the running API at a model endpoint that does not resolve,
drives a full citizen journey through the real HTTP surface, and compares the verdict
against a baseline captured moments earlier with the model configured.

```
1. Baseline — NSFDC_MICRO_FINANCE / ELIGIBLE (engine 2.2.0, rules 545b833da4e8f55d)
   rules fired: MF_CATEGORY_SC,MF_INCOME_CEILING,MF_NOT_FOR_EDUCATION,
                MF_PROJECT_COST_BAND,MF_LOAN_CAP_BINDS
2. Killing the language model → GROQ_BASE_URL=http://127.0.0.1:9/v1
3. A full citizen journey, model down
   ✓ Same scheme matched          ✓ Conversation still advanced (ASKING)
   ✓ Same verdict                 ✓ WhatsApp channel still replies
   ✓ Same rules fired, in order   ✓ Routing still works
   ✓ Same rules digest            ✓ Application submitted: SETU-2026-MH-000002
   ✓ Extraction fell back to      ✓ Tracking page renders
     the deterministic reader     ✓ Citizen was notified (1 message)

PASS — the core service degrades, it does not die.
```

The rules digest being byte-identical is the whole argument: **no model was ever involved
in deciding.** Only the wording changes. `--keep-down` leaves it broken to poke at.

### Tracing, logging, limits

One JSON object per line, one request ID per request, carried in a `ContextVar` so a log
line five layers down in the rule engine still reports which request it belonged to:

```json
{"ts":"2026-08-31T18:51:33+0000","level":"INFO","logger":"app.core.middleware",
 "msg":"request","request_id":"aac891c742834047","method":"GET",
 "path":"/api/v1/applications/NOPE","status":404,"duration_ms":96.04,"client":"172.18.0.1"}
```

The ID is returned in `X-Request-ID`, adopted from an upstream proxy when one sets it, and
included in every error body — so a citizen quoting a reference off an error screen gives
support one `grep`. uvicorn's own access log is *disabled* rather than reformatted: it
duplicated this line and ran outside the ContextVar scope, so its copy was always
untraceable.

Rate limiting is a fixed window in Redis, banded by route group — login hardest (10/min,
the only endpoint worth brute-forcing), the conversation next (30/min, it costs a model
call), everything else 120/min. It **fails open**: if Redis is unreachable the request is
served. Rate limiting exists to stop a runaway script, and a cache outage becoming an
eligibility outage is the wrong trade for a service people are relying on.

`GET /readyz` reports what the service can currently reach. Note the field name:

```json
{"database":"ok","redis":"ok","llm_provider_configured":"none",
 "llm_required_for_eligibility":false,"eligibility_available":true}
```

It reports *configuration*, not reachability, and is named so nobody reads `"groq"` during
an outage and concludes the model is answering. Probing the provider would put a paid,
multi-second call on a path an orchestrator hits every few seconds — and would not change
the answer, because eligibility does not depend on it.


## Vendored skills

`.claude/skills/` contains 376 skills vendored from
[alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills)
(MIT). `.claude/skills-manifest.json` records the upstream commit and the source path
of every skill. These are development aids for the team — they are not part of the
deployed application.

## Privacy, and how it is proved

CLAUDE.md rule 4 and the DPDP Act 2023: a government ID is masked at ingestion, and only
the last four digits plus a salted hash are retained. That claim is defended at four
layers and tested at every one of them.

| Layer | Defence | Where |
|---|---|---|
| Extracted text | `mask_text` rewrites every ID-shaped run | `app/services/redaction.py` |
| Image pixels | `redact_image` paints filled rectangles over the digits | `app/services/documents.py` |
| Persistence boundary | `assert_no_government_id` raises rather than writes | `app/services/redaction.py` |
| Database | `gov_id_last4 CHECK (~ '^[0-9]{4}$')`, `consent_id NOT NULL` | `app/models/citizen.py` |

The test that matters most renders an Aadhaar-like card, **confirms OCR can read the
number**, runs the real upload pipeline, and then OCRs the *stored bytes* to prove the
digits are gone from the pixels — the one layer a reviewer cannot verify by reading code:

```bash
docker compose exec api python -m pytest tests/test_redaction.py -v   # 18 tests
```

```
test_the_stored_image_no_longer_contains_the_number       PASSED
test_the_analysis_payload_carries_no_full_id              PASSED
test_an_id_document_is_refused_when_ocr_is_unavailable    PASSED
test_an_id_found_in_text_but_not_locatable_in_pixels_is_refused  PASSED
```

Against the live database after a full walk-through — submit, upload an Aadhaar card,
upload an income certificate, open the tracking page:

```
citizens              | AADHAAR | last4 0123 | hash 92d1711710828c39...
documents.ocr_extract | rows containing a full 12-digit ID: 0 of 2
audit_log.meta        | rows containing a full 12-digit ID: 0 of 49
stored image files    | OCR reads back: 'Governmentofindia Sunita Devi 1406/1988'
```

The number the card was rendered with is not in the database, not in the audit log, and
not in the pixels.

## Status

Phases 0 (foundation), 1 (eligibility engine), 2 (partner registry and geo routing),
3 (conversational intake), 4 (citizen frontend), 5 (applications and documents),
6 (partner console and ministry analytics) and 7 (reach, notifications, hardening) are
complete. See [CLAUDE.md](CLAUDE.md) for the engineering contract every phase must satisfy.

```bash
pytest packages/rules -q          # 116 tests — the eligibility engine and checklist
pnpm -r test                      # 46 tests — TS conformance, message ICU parity, storage
cd apps/api && pytest -q          # 338 tests — rules, redaction, auth, console, reach
pnpm --filter @setu/web check     # i18n parity, WCAG AA contrast, build, JS budget
```

The three OCR tests need tesseract, which ships in the API image but is unlikely to be on
your host — they skip locally and run in the container. To run the API suite there:

```bash
docker compose exec api pip install -r requirements-dev.txt   # pytest is not in the runtime image
docker compose exec api python -m pytest -q                   # 338 passed, 0 skipped
```

### The citizen app

Seven citizen routes: a language picker at `/`, then `/[locale]`, `/[locale]/assist`,
`/[locale]/results`, `/[locale]/results/[scheme]/partners`, `/[locale]/apply/[scheme]`
and `/[locale]/track/[ref]`. The staff consoles live outside the localised tree at
`/console/*` — that separation is structural, so a console dependency cannot end up in a
citizen bundle.

Lighthouse on the production build, mobile emulation with throttling:

| Route | Performance | Accessibility | Best Practices | SEO |
|---|---|---|---|---|
| `/en` | 100 | 100 | 100 | 100 |
| `/hi` | 100 | 100 | 100 | 100 |
| `/ta` | 100 | 100 | 100 | 100 |

FCP 0.8s · LCP 1.8s · TBT 0ms · CLS 0.

**JS budget: 114.4 KB gzipped of 200 KB** on the worst citizen route. Leaflet is ~150 KB
and is dynamically imported, so a citizen who never opens the map never downloads it.
`check:bundle` fails the build if a route crosses the line.

Three checks guard the things that are easy to regress silently:

- `check:i18n` — key parity across all six catalogues, every catalogue declaring whether
  it was reviewed, and no hardcoded English in a **citizen** component (the signed-in
  staff console is English-only and exempt; see OI-35)
- `check:contrast` — every foreground/background pair in the palette against WCAG AA,
  whether or not a page currently uses it
- `check:bundle` — gzipped First Load JS per citizen route

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
