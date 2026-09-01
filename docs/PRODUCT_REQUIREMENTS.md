# SETU — product requirements

**SIH 2026 · PS 26092 · Ministry of Social Justice & Empowerment**

> AI understands the citizen. Rules decide eligibility. Data routes the citizen.
> Evidence explains the decision.

Every requirement below carries its state as of the Phase 0 audit (2026-09-01): **built**,
**partial**, or **gap**. Nothing is marked built unless a test exercises it or it is
reproducible from `make demo`.

---

## Who this is for

**Primary — the citizen.** A Scheduled Caste entrepreneur or student, often on a Rs 6,000
Android over 2G, frequently not reading English fluently and sometimes not reading
fluently at all. They have been to a branch before and been turned away, and they will
not go twice.

**Secondary — the branch officer** at a Channel Partner, working a queue and needing to
know which case will actually move.

**Tertiary — the ministry analyst**, who needs to see where demand exists that supply
does not reach.

## The six questions the citizen surface must answer

These are acceptance criteria for the UI, not a design aspiration.

| # | Question | Where it is answered | State |
|---|---|---|---|
| 1 | What can I get? | Ranked scheme cards with an indicative amount | built |
| 2 | Why can I get it? | `matched_because[]`, every reason carrying a rule ID | built |
| 3 | Why can't I get the others? | Greyed ineligible cards with `blocked_because[]` | built |
| 4 | What do I need? | Personalised checklist with a reason per document | built |
| 5 | Where do I go? | Ranked partners, hard-filtered, with a score breakdown | built |
| 6 | What happens next? | Reference number, status timeline, notifications | built |

## Functional requirements

### FR-1 Eligibility is deterministic — built
A versioned rule engine decides. Same profile plus same ruleset gives a byte-identical
decision, reasons, warnings, redirect and next question. No network call, no model, no
randomness. Every decision carries `ENGINE_VERSION`, a rules digest, the rule IDs that
fired, and a timestamp.

Three-valued logic: an unknown field yields `NEED_MORE_INFO`, never a rejection.

### FR-2 The LLM may not decide — built
The model extracts facts and restates the engine's reasons. It may not invent
eligibility, approve, reject, invent a limit, rename a scheme, or imply approval.
Enforced structurally — the model is never handed the rupee figure — and covered by 36
tests in `test_llm.py`.

### FR-3 Scheme knowledge is data, not code — built
Schemes are versioned YAML with provenance per rule (`source_url`, `circular_ref`,
`effective_from`, `last_verified_on`, `needs_verification`). Adding a scheme is a data
change. Three families ship; the engine is indifferent to the count.

### FR-4 Conversational intake — built
Six languages, deterministic-first extraction, confidence gate at 0.7, uncertain values
become a confirmation question rather than a silent write. The session remembers the last
question and its choices, so a bare "SC" or a bare "80 hazaar" binds to the right field.

### FR-5 Indian-language numerals — built
Devanagari, Bengali, Tamil and Telugu digits; Indian comma grouping; `lakh`, `crore`,
`hazaar`; fraction words (`ढाई` = 2.5). 59 tests.

### FR-6 Explainable results — built
Reasons, warnings, redirects and the next action shown separately. Ineligible schemes are
displayed greyed with the blocking reason rather than hidden.

### FR-7 Transparent scheme ranking — **GAP**
Ranking today is a deterministic sort key — tightest fit, then cheapest, then most
generous, with the scheme code as a tiebreak for total order. It is correct and
reproducible. It is **not visible to the citizen**, who sees a rank and a confidence with
no account of why Scheme A beat Scheme B.

Required: a per-component score with the components shown, following the pattern already
proven for partner routing.

### FR-8 Channel Partner routing — built
Hard-filter first (authorisation, ticket size, service area, capacity), then rank on a
transparent composite — distance 0.40, turnaround 0.25, type affinity 0.20, load 0.15 —
with every component returned separately. `why_not[]` names the exact rule excluding each
nearby branch.

### FR-9 Geo intelligence — partial
PostGIS distance over a GIST index, 150km service radius, district coverage, underserved
districts. A citizen-facing map exists. The ministry view presents underserved districts
as a ranked table rather than a map.

### FR-10 Application lifecycle — built
`SETU-2026-MH-000431`. Nine states with an explicit transition table; an illegal
transition is refused with 409 and a message naming what is allowed from here.

### FR-11 Personalised documents — built
Narrowed by scheme family, partner type and known facts, with a stated reason per
document. An undecidable condition **includes** the document: an extra sheet of paper
beats a second trip.

### FR-12 Privacy — built
Four layers: text masking, pixel redaction, a persistence assertion that raises, and a
database CHECK constraint. Local OCR only. Fails closed. Proved by OCRing the stored
bytes, not by reading the code.

### FR-13 Partner console — built
Scoped by a WHERE clause rather than a permission check. Readiness with missing items
named, SLA clock against the partner's own stated turnaround, routing reasons re-rendered
in the officer's language, and a capacity toggle that feeds back into citizen routing.
Reject and request-documents require a reason.

### FR-14 Ministry dashboard — built
Funnel, misrouting prevented (broken down by exclusion rule), underserved districts,
scheme/language/status mix, turnaround by partner type, CSV export. Every figure is a
live query.

### FR-15 Low-bandwidth reach — built
`POST /api/v1/webhook/whatsapp` runs the same `handle_turn` as the web app. Numbered
menus, six languages, SMS segment accounting. Simulator at `/demo/whatsapp`.

### FR-16 Accessibility and offline — built
WCAG AA on every palette pair, 48px targets, visible focus, skip links, reduced motion,
voice input, read-aloud. The offline shell caches navigations and assets; **the API is
never cached**, because a stale eligibility verdict is worse than none.

### FR-17 Security and observability — built
Request IDs, structured JSON logs, banded rate limiting that fails open, a global error
boundary that never leaks a traceback, health and readiness endpoints, JWT with three
roles, append-only audit log.

### FR-18 Judge mode — **GAP**
No `/demo` mission-control page. Scenarios must currently be driven by hand, which is a
risk under time pressure in front of a jury.

## Non-functional requirements

| Requirement | Target | State |
|---|---|---|
| Citizen route JS | < 200 KB gzipped | 114.4 KB — built |
| Lighthouse (production, mobile) | 90+ | 100/100/100/100 — built |
| Eligibility without a model | must work | proved by `make chaos` — built |
| Clean start | `docker compose up` from a clean clone | 37–44 s — built |
| Deterministic demo | no randomness, no external API | fixed seed — built |
| Eligibility p95 | < 500 ms | **not measured — gap** |

## Explicit non-goals

- SETU does **not** approve loans. It matches and routes; a Channel Partner decides, and
  every screen says so.
- No autonomous agents, no multi-agent orchestration, no blockchain, no opaque ML
  scoring. Each adds surface area without answering any of the six questions.
- No fake government API. Where data is synthetic it is labelled synthetic.

## Data integrity classes

| Class | Meaning | How it is marked |
|---|---|---|
| Verified | Traced to a public NSFDC source, dated | `needs_verification: false` plus `source_url` |
| Unverified | Believed correct, no citable source | `needs_verification: true`, badged in the UI |
| Synthetic | Invented for the demo | Disclaimer on every screen that renders it |

The 120 Channel Partners are **synthetic**. Scheme figures are **verified** against
nsfdc.nic.in as of 2026-08-29 but carry no circular number, so they stay flagged.
