# SamarthSetu — test strategy

**632 tests.** What they cover, what they deliberately do not, and where the gaps are.

| Suite | Count | Runner |
|---|---|---|
| API | 434 | `cd apps/api && pytest -q` |
| Rule engine | 152 | `pytest packages/rules -q` |
| TypeScript | 46 | `pnpm -r test` |

Plus five build-failing checks and one runtime drill (`make chaos`).

---

## What we test for, in priority order

**1. Anything a citizen would be harmed by getting wrong.** A wrong verdict, a leaked
Aadhaar number, a message that promises approval. These get the most tests and the most
adversarial ones.

**2. Anything that fails silently.** A notification dropped by a fail-open guard, an
audit row that stops being written, a hydration mismatch that only exists in a browser.
Every one of these has actually happened here, and each now has a test.

**3. Anything that is easy to regress and invisible in review.** SMS segment arithmetic,
ICU placeholder parity across six catalogues, the Python ≡ TypeScript engine equivalence.

We do not chase coverage percentage. A test that asserts a getter returns what was set
costs maintenance and buys nothing.

---

## Rule engine — 116 tests

| File | Tests | What it holds |
|---|---|---|
| `test_engine.py` | 26 | Verdict logic, ranking determinism, the three personas |
| `test_boundaries.py` | 17 | Every threshold at, just below, and just above |
| `test_versioning.py` | 15 | Engine version and pinned digest; policy cannot shift quietly |
| `test_documents.py` | 14 | Checklist narrowing, six languages, provenance |
| `test_safe_eval.py` | 13 | AST whitelist, Kleene logic, `bool(UNKNOWN)` raises |
| `test_next_best_question.py` | 10 | Question selection, the `exclude` set |
| `test_golden.py` | 2 | Frozen snapshot of every persona's full output |

**Boundary testing is exhaustive on purpose.** A ceiling of ₹1,40,000 is tested at
139,999 / 140,000 / 140,001. Off-by-one on a scheme ceiling is a citizen wrongly refused.

**Determinism is asserted, not assumed.** The golden snapshot means any change to a
verdict, a reason, an order or a digest fails CI and has to be deliberate.

## LLM safety — 36 tests

This is the suite that defends the project's central claim. Every test exists because a
live model did the thing it prevents.

- Prose that renames the official scheme is rejected
- Prose claiming approval is discarded — in English and in Hindi
- The model is never shown the amount; the amount sentence is appended by us
- The extraction tool schema offers no money field to any provider
- A value outside the vocabulary is dropped, not coerced
- A lowercase enum from a model is normalised rather than 422-ing the whole turn
- A provider error degrades instead of raising; extraction and explanation both fall back
- `describe()` never leaks a key

### Adversarial: a model that is present and hostile — 13 tests

`test_llm_cannot_override.py` runs the real orchestration path against a stubbed provider
that returns approvals, inflated amounts, renamed schemes and fabricated eligibility, and
asserts the deterministic output is unchanged. It cannot invent a scheme, inflate the
amount past the loan cap, make an ineligible citizen eligible, or touch the engine version
or rules digest.

The last test in that file is the one that makes the rest mean anything:

```
test_the_hostile_model_is_actually_reached
```

Every other assertion says "the hostile output did not get through" — and all of them
would also pass if the model were never called at all. That test counts the calls.

## Privacy — 18 tests

Layered to match the four defences, and the important one is not readable from the code:

```
test_the_stored_image_no_longer_contains_the_number
```

It renders an Aadhaar-like card, **asserts OCR can read the number** (so a pass means
redaction removed it, rather than OCR never having seen it), runs the real pipeline, then
OCRs the *stored bytes*.

Also covered: every Aadhaar spelling masked, PAN and voter ID, salted hash stability and
irreversibility, nested payload scanning, the fail-closed paths, and the honest limit —
an ID document with no readable number is stored with a warning, and a test pins that
behaviour so it cannot change by accident.

## Conversation and language — 32 tests

Six languages, numeral parsing across four scripts, Indian comma grouping, scale words,
fraction words. Confirmation flow: uncertain readings become questions; declining does
not write; confirming does.

One test is written as a *narrower invariant than the obvious one*: a question may repeat
only when no other field could change any rule. The blanket "never repeat" assertion was
too strong — once every other field is known, the unanswered one is the only thing
between the citizen and a verdict.

## Routing, console, applications — 51 tests

Authorisation, ticket size, district, distance, capacity, ranking determinism. The
console's action vocabulary is checked against the lifecycle transition table, so a button
that could never legally be pressed fails CI. Every legal and illegal transition is
exercised.

## Hardening — 13 tests

JSON log shape (including that an unserialisable `extra` still produces a line — a logger
that raises loses the message you needed), request ID uniqueness, rate-limit banding, and
that health and docs are never metered.

## Frontend — 46 tests

| File | Holds |
|---|---|
| `messages.test.ts` | ICU placeholder parity across six catalogues, no empty strings, official names not translated |
| `format.test.ts` | Indian lakh grouping, not Western thousands |
| `storage.test.ts` | Survives a throwing `localStorage`, a full quota, corrupted JSON |
| `conformance.test.ts` | The TypeScript engine agrees with Python, from the compiled rule AST |

Placeholder parity matters because key-parity checking passes while a Tamil string that
dropped `{count}` renders a sentence with a hole in it.

## Build-failing checks

| Check | Catches |
|---|---|
| `check:i18n` | Missing keys, undeclared review status, hardcoded English in a citizen component |
| `check:contrast` | Any palette pair below WCAG AA, whether or not a page uses it yet |
| `check:hydration` | Non-deterministic values in a `useState` initialiser or JSX — including one level behind a helper |
| `check:bundle` | Gzipped First Load JS per citizen route against a 200 KB budget |
| `next build` | Types and compilation |

`check:hydration` exists because we shipped that bug and `tsc`, ESLint, the build and all
46 tests passed with it present. It only existed in a browser.

## The chaos drill

```
make chaos
```

Points the running API at a model endpoint that does not resolve and drives a full
journey through the real HTTP surface — match, conversation, WhatsApp, routing,
application, tracking, notification. Asserts the scheme, verdict, rule order and **rules
digest** are byte-identical to a baseline taken moments earlier with the model configured.

## Test isolation

`tests/conftest.py` disables every provider for every test. Without it, a machine with
`GROQ_API_KEY` exported runs the suite against a live provider: one real run took 407
seconds and produced four spurious failures.

## Security surface — 82 tests

`test_security_surface.py` drives the running API over real HTTP, the way `chaos.sh`
does, and skips cleanly when nothing is running. Injection-shaped strings into every
unauthenticated endpoint, malformed and oversized bodies, wrong types, deep nesting,
control characters, five scripts. Then: no traceback in any error, a request ID on every
response, identical 404 wording so a reference number cannot be enumerated, every console
endpoint refusing an anonymous caller, `alg: none` refused, a partner token refused at the
ministry dashboard, and a **live 429** proving the Redis round trip.

The in-process route was tried first and abandoned. `TestClient` starts a fresh event
loop per request while the app's async engine is a module-level singleton bound to the
first loop, so every request after the first failed with "attached to a different loop" —
500s the real service does not produce. Testing over the wire avoids that and exercises
more.

**It found a real bug on its first run.** A NUL byte — legal in JSON as ` `, legal
in a URL as `%00` — passed Pydantic, passed the rule engine, and died inside asyncpg,
because Postgres `text` and `jsonb` cannot store one. A 500 on a public, unauthenticated
endpoint. Now rejected at the edge with a 400, and pinned by two tests.

## Known gaps

| Gap | Why it is open |
|---|---|
| No browser-level LLM-equivalence test | Covered at the service layer and by `make chaos` |
| No browser E2E (Playwright) | Deliberate: high maintenance for a hackathon build. Routes are smoke-checked by HTTP status |
| No eligibility p95 measurement | The NFR is stated and unverified |
| OCR unproven on real photographs | OI-32. Proved on rendered cards only |
| No accessibility test beyond contrast | Lighthouse scores 100, but that is a snapshot, not a gate |
