# Open items

Known gaps, blockers, and deliberate omissions. Every entry says what is missing, why
it is missing, who can close it, and what breaks if it stays open.

Nothing here is a surprise on demo day if it is read first.

**Legend** — 🔴 blocks the demo · 🟡 weakens the demo · 🟢 tracked, not urgent

Last reviewed: 2026-09-04 (after the account surface and design port)

---

## 🔴 OI-1 — `docker compose up` has never been run

**Status:** CLOSED 2026-08-29 · **Owner:** repo owner · **Since:** Phase 0

Docker Desktop was installed and the full stack verified end to end:
**39 seconds from `docker compose down -v` to a healthy stack.**

| Verified against the running system | |
|---|---|
| PostGIS + pgvector in one image | `postgis 3.4.3`, `vector 0.8.6` |
| `alembic upgrade head` on a real database | applied cleanly, 11 tables + `alembic_version` |
| GIST indexes | `ix_channel_partners_geom`, `ix_citizens_geom` |
| GIN index | `ix_partner_scheme_authorisations_service_districts` |
| `GET /health` | `200 {"status":"ok"}` |
| `GET /docs` · `GET /` | `200` · `200` |
| Seed runner in-container | extensions verified, 0 seeders registered (correct for this phase) |

Four bugs were found and fixed only because the stack was actually run — see the Closed
table (OI-12 through OI-15).

---

## 🔴 OI-2 — no git repository in the project directory

**Status:** CLOSED 2026-08-29 · **Owner:** repo owner · **Since:** Phase 0

`git rev-parse --show-toplevel` returned `C:/Users/anike` — the enclosing repo was the
user's home directory, whose only commit was an empty `README.md`. Zero project files
were tracked, so the per-phase commit discipline ("judges do look at commit history")
could not work.

Closed by running `git init` in the project directory and committing the work to date.
See OI-9 for the remaining history caveat.

---

## 🟡 OI-3 — no NSFDC circular number for any scheme

**Status:** partially closed 2026-08-29 · **Owner:** needs a domain contact

Originally every figure came from the SIH problem statement alone, with `source_url`
and `circular_ref` null. **Resolved on 2026-08-29** by verifying against
[nsfdc.nic.in/scheme](https://nsfdc.nic.in/scheme) and
[nsfdc.nic.in/eligibility-requirements](https://nsfdc.nic.in/eligibility-requirements):
amounts, interest rates, tenure, moratorium, and the Rs 5,00,000 income ceiling
(stated there as effective 2026-01-07) are now sourced.

**Still open:** no scheme circular *number* has been located, so `circular_ref` and
`effective_from` remain null and all three schemes keep `needs_verification: true`.
Each scheme file records its remaining unknowns in `provenance.open_questions`, and
`test_versioning.py` fails if any scheme leaves an unknown undeclared.

**If it stays open:** figures are attributable to a government website but not to a
dated circular. Acceptable for a hackathon; not acceptable for a pilot.

---

## 🟡 OI-4 — four of six languages are untranslated

**Status:** REDUCED 2026-08-29 · **Owner:** needs a human reviewer · **Since:** Phase 1

All six languages now have complete copy: rule messages, question text, explanation
templates, confirmation prompts, approval blocklists and extraction cues, in
`packages/rules/translations/<lang>.yaml`, one file per language.

**They are `status: draft` — written by a language model, not read by a native speaker.**
That status is not a comment: it is carried on every `MatchResult` as
`translation_status` and out through the API, so a UI can badge unreviewed copy and a
deployment can tell verified from draft.

**What remains is review, not authoring.** A fluent speaker reads one file per language
and flips `status: verified`. See
[packages/rules/translations/README.md](../packages/rules/translations/README.md) for
the checklist.

**If it stays open:** the demo works in six languages, but only English and Hindi copy
has been checked by a person. Say "six languages, two reviewed" rather than "six
languages".

### Original entry

`en` and `hi` are complete for every rule message. `mr`, `bn`, `ta`, and `te` are
declared in each scheme file's `pending_translations` and **fall back to English at
runtime**.

This is deliberate. A wrong eligibility reason in Tamil is worse than a correct one in
English, and these strings tell a citizen why they were refused credit. They are not
UI chrome. `test_versioning.py` enforces en/hi completeness and asserts the other four
are declared rather than silently missing.

**To close:** a human fluent in each language translates the `message_i18n` and
`satisfied_i18n` blocks in `packages/rules/schemes/*.yaml`, then removes that language
from `pending_translations`.

**If it stays open:** CLAUDE.md's six-language commitment is half-met, and Phase 4
cannot honestly claim six languages. Say so in the pitch rather than letting a judge
find it.

---

## 🟡 OI-5 — Educational Loan cap may vary by study location

**Status:** open · **Owner:** needs a domain contact · **Since:** Phase 1

The NSFDC scheme page states a single cap: *"Upto Rs 40.00 Lakh or 90% of course fee,
whichever is less."* Secondary sources describe **Rs 30,00,000 for study in India** and
**Rs 40,00,000 for study abroad**. The engine records only the official single figure
and does not model a split, because assuming one would be inventing policy.

**To close:** confirm whether the cap varies, and if so add a study-location field to
the profile contract and a rule that selects the right cap.

**If it stays open:** a student studying in India may be shown an indicative amount up
to Rs 10,00,000 too high.

---

## 🟢 OI-6 — Term Loan moratorium is activity-dependent

**Status:** open · **Owner:** Phase 2+ · **Since:** Phase 1

NSFDC states a 6-month moratorium generally and 12 months for plantation and
construction activities. The engine holds the 6-month figure because the profile has no
field for activity type. Recorded in the scheme's `open_questions`.

---

## 🟢 OI-7 — Educational Loan tenure is not a single number

**Status:** open · **Owner:** Phase 2+ · **Since:** Phase 1

NSFDC states 12 years where repayment has not started and 10 years where the loan has
been disbursed, with a moratorium of "course period plus one year". Neither reduces to
one integer, so both `tenure_months` and `moratorium_months` are null rather than
approximated.

---

## 🟢 OI-8 — the rule engine is not yet wired into the API

**Status:** CLOSED 2026-08-29 · **Owner:** Phase 2 · **Since:** Phase 1

`POST /api/v1/match` calls the engine and writes a `match_runs` row plus an `audit_log`
entry on every call. The Docker build context moved to the repo root so the image can
`pip install -e /packages/rules` — the container runs the same rule pack the tests do,
rather than a path-hacked copy.

---

## 🟡 OI-27 — the citizen app has only been tested in a browser engine

**Status:** open · **Owner:** needs a real device · **Since:** Phase 4

Lighthouse scores 100 across performance, accessibility, best practices and SEO on the
production build under mobile emulation with throttling, and the JS budget is enforced
in CI at 113.9 KB of 200 KB gzipped.

What has **not** been tested is the thing CLAUDE.md actually names: a Rs 6,000 phone on
a 2G connection, one-handed, in sunlight. Emulated throttling is not the same as a
cheap Android device with a slow CPU and a weak radio, and no emulator tells you whether
a 48px target is reachable with a thumb or whether the palette survives direct sun.

Specifically unexercised: Web Speech API recognition on a low-end Android browser (it is
feature-detected and falls back to typing, but the fallback is what has been tested, not
the speech path), and the service worker's offline behaviour on a real flaky connection
rather than DevTools' offline toggle.

**To close:** run the full flow on the cheapest Android phone available, outdoors, on a
throttled connection.

---

## 🟡 OI-28 — five of six web catalogues are unreviewed

**Status:** open · **Owner:** needs a human reviewer · **Since:** Phase 4

`apps/web/messages/*.json` mirrors the rule-engine translation discipline: 88 keys per
language, `_meta.status` on every catalogue, and `check:i18n` failing the build if a key
is missing or a status is undeclared. English and Hindi are `verified`; Marathi, Bengali,
Tamil and Telugu are `draft`.

The language picker badges draft languages, and the results page carries a banner
saying the wording has not been checked. That is honest, not a substitute for review.

Same fix as OI-4: a fluent speaker reads one file and flips the status.

---

## 🟡 OI-19 — the LLM path has never been executed

**Status:** CLOSED 2026-08-29 · **Owner:** needs an API key · **Since:** Phase 3

Exercised live against **Groq** (`qwen/qwen3.8-27b`), both operations passing. Running a
Hindi conversation with the model live produced **byte-identical verdicts** to calling
the engine directly — the equivalence claim now holds against a real model, not only a
stub.

Three defects surfaced that only a live model could reveal; all three are fixed and
regression-tested:

1. The model returned `gender: "female"` where the contract requires `FEMALE`. That
   raised in `validate_profile` and failed the whole turn with a 422. Values are now
   coerced to the contract, or dropped — a model quirk cannot break a conversation.
2. It wrote **"मिनी फाइनेंस स्कीम"** for the Micro Finance Scheme, machine-translating a
   legal scheme name, which CLAUDE.md forbids. Explanations whose official name did not
   survive are now discarded in favour of the template.
3. It wrote that the amount "can now be released", implying sanction. The service
   matches and routes; a Channel Partner decides. The prompt now forbids approval
   language explicitly.

**Update 2026-08-29 (later):** (3) is no longer prompt-level. The model is no longer
given the rupee figure at all — `amount_sentence()` renders it in wording this service
controls and appends it after the model's prose — so "the amount will be released" is
unreachable rather than discouraged. A narrow multilingual blocklist backstops prose
that claims an approval without quoting a figure, and a test asserts our own template
never trips it.

A fourth defect surfaced in the same live run: `redirect_suggestion` is an internal code,
and the model faithfully printed **"NSFDC_MICRO_FINANCE"** to the citizen. Codes are now
resolved to official names before they reach either the model or the template.

**Residual risk:** the approval blocklist covers English and Hindi. Marathi, Bengali,
Tamil and Telugu prose is unguarded against approval phrasing, which is the same gap as
OI-4 and OI-20 — those languages have no reviewed copy anywhere in the system yet.

### Original entry

No provider key is set, so extraction and explanation run their deterministic and
template paths only. Those paths are fully tested and carry the demo.

**Update 2026-08-29:** the provider is now pluggable
(`LLM_PROVIDER=auto|anthropic|xai|groq|none`) with xAI and Groq both reached over their
OpenAI-compatible endpoints, and `scripts/check_llm.py`
makes a real text and tool call so a broken key can be told apart from no key. Provider
resolution and every failure-to-fallback path are unit-tested. The remaining gap is
narrower than before: no live call to any vendor has yet been made.

What is **not** exercised: the Anthropic tool-use call in `extraction.extract_with_llm`,
the prose call in `explanation.explain`, and guardrail behaviour against a real model
response. `_validate_llm_fields` is unit-tested against synthetic payloads, so the
guardrail logic is covered even though the call is not.

**To close:** put a key in `.env` (`GROQ_API_KEY=`, `XAI_API_KEY=` or
`ANTHROPIC_API_KEY=`), restart the
API, run `scripts/check_llm.py` until both probes pass, then run a conversation using
free text the keyword tables do not cover.

**If it stays open:** the demo still works end to end, but "the LLM extracts facts" is
an untested claim. Say "deterministic extraction with optional LLM enrichment", which is
what is actually running.

---

## 🟢 OI-20 — extraction keyword tables are hand-built

**Status:** REDUCED 2026-08-29 · **Owner:** Phase 4+ · **Since:** Phase 3

Marathi, Bengali, Tamil and Telugu cue vocabulary now ships in each language bundle's
`cues:` block, additive to the inline English and romanised-Hindi tables (a citizen may
type either while asking for answers in Tamil). Still hand-built and still draft.

### Original entry

Sector, category, gender and place detection use curated keyword lists covering English,
romanised Hindi and Devanagari. Marathi, Bengali, Tamil and Telugu cue words are absent,
so in those languages extraction currently leans on the numeral parser (which does cover
their digits) plus the LLM path, itself unexercised (OI-19).

Related to OI-4: the same four languages lack rule-message translations.

---

## 🟡 OI-29 — the citizen flow has not been walked on a real phone

**Status:** open · **Owner:** repo owner · **Since:** Phase 4

Lighthouse scores 100 across the board under mobile emulation and throttling, and every
route returns 200. What has **not** happened is a human completing the journey on an
actual low-end Android phone on a real 2G/3G connection.

Specifically unexercised: Web Speech API recognition (emulation cannot test a
microphone), the service worker's offline path against genuine connection loss rather
than devtools, and whether 48px targets are actually comfortable one-handed in sunlight.

**To close:** open the deployed URL on a cheap Android handset, speak an answer, walk
into a dead spot, and confirm the offline banner and saved results appear.

---

## 🟢 OI-18 — routing weights are unvalidated judgement

**Status:** open · **Owner:** needs field input · **Since:** Phase 2

Distance 0.40, turnaround 0.25, type affinity 0.20, load 0.15. These are a reasonable
first guess, not a measured optimum, and the type-affinity table encodes how the
Channel Finance System is *described* rather than observed throughput.

They are deliberately in one config file and returned in every routing response so a
ministry reviewer can argue with them without reading code.

**To close:** validate against real disbursement outcomes — which routings actually led
to a sanction — once any real application data exists.

---

## 🟢 OI-9 — commit history is retrospective, not per-phase

**Status:** accepted · **Since:** Phase 1

Because the repository was created after Phases 0 and 1 were already written (OI-2),
the history opens with a small number of squashed commits rather than an organic
per-phase trail. From Phase 2 onward, commits are made as work lands.

---

---

## 🟡 OI-31 — the document checklist has no circular behind it

**Status:** open · **Owner:** needs MoSJE/NSFDC input · **Since:** Phase 5

`packages/rules/documents/checklist.yaml` lists 13 documents with a reason for each. The
list is assembled from what NSFDC channel partners publish on their own application
pages, not from a scheme circular. `needs_verification: true` is set on the file and the
API returns it on every checklist response, so the UI says "this is our reading of what
offices usually ask for — confirm at the branch" rather than stating it as a rule.

The validity windows are the softer half of this. Where a window is common partner
practice rather than published policy, `validity_is_practice_not_rule` is set and the
citizen is told "most offices ask for one issued within N months", not "must be".

**Breaks if it stays open:** a citizen carries a document they did not need, or is told a
certificate is stale on our authority rather than the partner's.

**To close:** obtain the current NSFDC channel-partner documentation circular and set
`source_url` / `circular_ref` / `needs_verification: false`.

---

## 🟡 OI-32 — OCR quality on a real photograph is unmeasured

**Status:** open · **Owner:** repo owner · **Since:** Phase 5

Redaction is proved against a **rendered** card: clean black text, white ground, no
skew, no glare. That proves the pipeline works. It does not prove tesseract finds the
number on a creased Aadhaar card photographed at an angle in a dim room, which is what
will actually arrive.

The failure mode is asymmetric and it is the bad direction: if OCR cannot read the
number, `find_government_ids` returns nothing, nothing is painted, and the image is
stored **unredacted** — because from the code's point of view there was no ID to mask.
The `ids and painted == 0` guard only fires when the text extractor sees a number the
pixel locator cannot place. It does not fire when neither sees anything.

**Breaks if it stays open:** a blurred Aadhaar card is stored with a number a human can
still read even though tesseract could not.

**To close:** photograph 20 real ID documents in realistic conditions, measure the
detection rate, and if it is not near-total, treat `doc_type == IDENTITY_PROOF` with no
detected ID as suspicious — refuse it, or store it blurred wholesale rather than trusting
a negative result.

---

## 🟢 OI-33 — Phase 5 copy is new in all six languages, including Hindi

**Status:** open · **Owner:** needs a reviewer per language · **Since:** Phase 5

`apply.*` and `docs.*` (27 new keys) were written for this phase in all six catalogues.
`hi` is declared `verified` because the catalogue as a whole was reviewed in Phase 3, but
these particular strings have not been read by a Hindi speaker since they were added.
The four draft locales are covered by OI-4; this notes that Hindi now has the same gap
for the new keys specifically.

`src/i18n/messages.test.ts` catches the mechanical half — a locale that drops or renames
an ICU placeholder, or leaves a string empty — but says nothing about whether the Tamil
for "we keep only the last 4 digits" reads naturally.

**To close:** fold these keys into the same review pass as OI-4.

---

---

## 🔴 OI-35 — the staff console is English-only

**Status:** open · **Owner:** needs a reviewer per language · **Since:** Phase 6

`/console/partner` is a desk tool for a Channel Partner branch officer, and its chrome —
buttons, headings, column names — is English. A branch officer in Tamil Nadu or West
Bengal is precisely the user this project claims to serve, so this is a real gap, not a
scoping nicety.

What *is* localised is the part that carries meaning: the rule-engine reasons an officer
reads are rebuilt from stable rule IDs in the officer's language, so "why was this routed
here" is answerable in all six. `scripts/check-i18n.mjs` now states its scope explicitly
(citizen components) and exempts `src/app/console` rather than silently passing.

**Breaks if it stays open:** a branch officer who does not read English can still process
applications — the reasons and the citizen's details are translated — but navigates the
tool by position rather than by reading it.

**To close:** add a `console` namespace to the six catalogues, in the same review pass as
OI-4 and OI-33.

---

## 🟡 OI-36 — the 25km coverage radius is our number, not a policy one

**Status:** open · **Owner:** needs MoSJE input · **Since:** Phase 6

`analytics.COVERAGE_RADIUS_KM = 25.0` decides which districts the ministry dashboard
calls underserved. It is a reasonable "can reach a branch and get home the same day"
guess, and it is not from any circular. It sits beside `MAX_SERVICE_RADIUS_KM = 150`
in the routing engine, which is a different unvalidated number for a different purpose
(OI-18).

The dashboard returns `radius_km` in every response so a reviewer can see what the figure
was computed against rather than having to trust the label.

**Breaks if it stays open:** a district is named underserved, or not, on our arithmetic
rather than the ministry's definition of reach.

**To close:** get the accessibility standard MoSJE actually uses for branch coverage.

---

## 🟡 OI-37 — role changes take up to an hour to take effect

**Status:** accepted, documented · **Since:** Phase 6

A JWT carries the role and lives for `ACCESS_TOKEN_EXPIRE_MINUTES` (60). `deps.current_user`
re-reads the user from the database on every request, so **deactivating an account is
immediate** — but a *role* change is not reflected until the token is reissued.

At one hour that is an acceptable window for a hackathon build with three seeded accounts,
and it is written down here so nobody later assumes revocation is instant. Real
deployment replaces this entirely with NIC / Parichay SSO.

**To close:** not by hand-rolling refresh tokens. This closes when SSO lands.

---

---

## 🟡 OI-43 — no notification can actually leave the building

**Status:** open, deliberate · **Owner:** needs a product + DPDP decision · **Since:** Phase 7

Phase 5 stores `phone_last4` and nothing more, because at that point nothing needed to
contact the citizen. Phase 7 needs to, and the schema will not support it: `SmsDriver`
and `WhatsAppDriver` implement the full interface and raise `ContactUnavailable`, because
a driver that returned `SENT` would put a green tick beside a message nobody received.

The in-app channel is not a workaround dressed up as a virtue — it needs no address, so
it leaks nothing, works offline, and cannot be read off a shared handset. But it only
reaches a citizen who comes back to the tracking page, and the whole point of a
notification is reaching someone who has not.

**To close, deliberately rather than by accident:** add a delivery number under its own
consent purpose (not the eligibility purpose), stored encrypted with `phone_last4` kept
for display, revocable independently, and excluded from every console response the way
`gov_id_hash` already is. Then set `NOTIFICATION_DRIVER=sms`.

---

## 🟢 OI-44 — rate limiting is per-IP, and a village shares one

**Status:** open · **Owner:** repo owner · **Since:** Phase 7

The limiter buckets on `request.client.host`. Behind carrier-grade NAT — which is most
mobile data in India — a whole town can present as one address, so a busy afternoon in a
district could look like one client exceeding 120 requests a minute.

It fails open on a Redis outage but *not* on this: the counter would be perfectly
functional and perfectly wrong. The limits are set high enough that it is unlikely at
demo scale, and the failure is a 429 with a `Retry-After`, not a lost application.

**To close:** bucket on the session id where one exists and fall back to IP only for
unauthenticated first contact, or trust `X-Forwarded-For` from a known proxy only.

---

---

## 🟡 OI-48 — never deployed to a public URL

**Status:** open, deliberate · **Owner:** repo owner · **Since:** Phase 8

The Phase 8 spec asks for a live URL verified from a phone on mobile data. The configs
are checked in and complete (`apps/web/vercel.json`, `render.yaml`,
[DEPLOYMENT.md](DEPLOYMENT.md) with the PostGIS/pgvector step Render will not do for you)
but nothing has been deployed: that needs accounts and credentials belonging to the
repository owner, and publishing a government-adjacent service is a decision to take
deliberately rather than a side effect of a build.

Consequences worth knowing before deploying, all listed in DEPLOYMENT.md: `SECRET_KEY`
defaults to `change-me`, `ID_HASH_SALT` falls back to it, the login page prints demo
credentials, and `STORAGE_DIR` is a local path that an ephemeral filesystem loses on
redeploy.

**Also unclosed by this:** OI-29, walking the citizen flow on a real low-end Android over
mobile data. Lighthouse's throttling is a model of a bad connection, not a bad connection.

**To close:** run the DEPLOYMENT.md checklist, deploy, put the URL at the top of the
README, and open it on a cheap handset away from office wifi.

---

## Closed

| ID | Item | Closed |
|---|---|---|
| OI-2 | No git repository in the project directory | 2026-08-29 |
| OI-10 | `packages/rules/dist/rules.json` was gitignored, so CI would fail on a fresh clone — the TypeScript conformance test imports it. `.gitignore` now re-includes it. | 2026-08-29 |
| OI-11 | `max_amount` conflated the project-cost band with the loan cap, overstating what a citizen could borrow (Rs 1,26,000 shown against a Rs 1,25,000 real cap). Split into `max_project_cost` and `max_loan_amount` in engine v2.0.0. | 2026-08-29 |
| OI-1 | `docker compose up` never run — Docker not installed | 2026-08-29 |
| OI-12 | Shell scripts and Dockerfiles were checked out CRLF on Windows, so `#!/usr/bin/env bash\r` would have failed in-container as `bad interpreter`. Added `.gitattributes` forcing LF. | 2026-08-29 |
| OI-13 | `apps/web` had no `.dockerignore`, so `COPY . .` copied the host pnpm workspace `node_modules` whose symlinks point at Windows absolute paths, clobbering the Linux install. The web container died with `Cannot find module '/app/node_modules/next/dist/bin/next'`. | 2026-08-29 |
| OI-14 | `scripts/seed/run.py` assumed the host layout (`<repo>/apps/api`) and could not import `app` inside the container, where the API is at `/app`. Now tries both. | 2026-08-29 |
| OI-15 | `sentence-transformers` in `apps/api/requirements.txt` pulled ~2GB of torch into the API image while nothing imported it. Moved to `requirements-ml.txt` for Phase 2+. | 2026-08-29 |
| OI-8 | Rule engine not wired into the API | 2026-08-29 |
| OI-19 | LLM path never executed — closed against Groq | 2026-08-29 |
| OI-22 | An LLM returning a correct value in the wrong shape (`"female"` for `FEMALE`) failed the entire conversational turn with a 422. Values are now coerced to the profile contract or dropped. | 2026-08-29 |
| OI-24 | The model was handed the rupee amount and phrased it as a disbursement. It is no longer given the figure at all; the amount sentence is rendered by us and appended. | 2026-08-29 |
| OI-29 | The API test suite made live model calls on any machine with a provider key exported — four failures and a seven-minute run instead of one second. A `conftest.py` autouse fixture now forces the provider off for every test. | 2026-08-29 |
| OI-30 | `ink-faint` on the page ground was 4.34:1, under WCAG AA. Darkened to 5.33:1, and `check:contrast` now tests every palette pair rather than only colours Lighthouse happens to see. | 2026-08-29 |
| OI-27 | Tests hit a live LLM provider whenever a developer had a key exported — one run took 407s and produced 4 spurious failures. `tests/conftest.py` now disables every provider for the whole suite. | 2026-08-30 |
| OI-28 | `ink-faint` on the page ground was 4.34:1, under WCAG AA. Darkened to 5.33:1, and `check-contrast.mjs` now tests every palette pair rather than only what Lighthouse happens to see. | 2026-08-30 |
| OI-26 | The API response schema silently dropped `translation_status`, so a UI could not tell reviewed copy from machine-written copy. Added to `MatchResultOut`. | 2026-08-29 |
| OI-25 | `redirect_suggestion` carried an internal scheme code, which the model printed to the citizen as "NSFDC_MICRO_FINANCE". Codes now resolve to official names before reaching the model or the template. | 2026-08-29 |
| OI-23 | An LLM machine-translated the official scheme name into Hindi. Explanations that do not preserve the official name verbatim are now discarded. | 2026-08-29 |
| OI-21 | The orchestrator asked the same question three turns running when a citizen did not answer it. `next_best_question` now takes an `exclude` set, in both the Python and TypeScript engines. | 2026-08-29 |
| OI-16 | Partner service areas were random districts within a state, so a Mumbai branch "served" Nagpur 687km away and the router ranked it. Service areas are now the geographically nearest districts, and routing rejects anything beyond a 150km radius with a stated reason. | 2026-08-29 |
| OI-17 | 120 partners spread uniformly over 53 districts left Nagpur with a single branch, making routing look empty. Seeding now guarantees one partner per district and weights the remainder towards large cities. | 2026-08-29 |
| OI-34 | `apps/web` shipped a `test: vitest run` script with zero test files in Phase 4, so `pnpm test` — a stated definition-of-done gate — failed from a clean clone. Added 27 tests covering rupee grouping, offline storage under a throwing `localStorage`, and ICU placeholder parity across all six catalogues. | 2026-08-30 |
| OI-38 | Alembic's `include_object` filtered PostGIS tables by *name*, which missed the `tiger` and `tiger_data` schemas entirely — and because `postgis_tiger_geocoder` puts itself on the database `search_path`, autogenerate saw ~30 of its tables as unqualified and emitted `op.drop_table` for every one. The search_path is now pinned to `public` as an asyncpg server setting. | 2026-08-30 |
| OI-39 | Fixing OI-38 with `SET search_path` on the connection started an implicit transaction that alembic's own `begin_transaction()` did not own: the migration was rolled back while alembic reported `Running upgrade ... done`. Caught because the table was absent afterwards. | 2026-08-30 |
| OI-40 | A routing call served from the Redis cache returned early and wrote **no audit row**, so both the anti-misrouting KPI and the CLAUDE.md rule 4 "who read what" trail silently undercounted exactly when the system was busiest. | 2026-08-30 |
| OI-41 | The anti-misrouting KPI was derived from `why_not`, which is truncated to the nearest few for the citizen UI — one routing call that excluded 59 partners contributed 3. The routing result now carries a full `rejected_by_reason` tally. | 2026-08-30 |
| OI-42 | A partner pausing intake left the routing cache serving the old capacity for its TTL, which on a live demo is the worst possible moment to be stale. `cache.invalidate_routing()` now runs on every capacity change. | 2026-08-30 |
| OI-45 | A bare amount answering a direct question was bound to the wrong field: asked "how much do you need?", a citizen replying "80 hazaar" had it read as an annual **income** of Rs 80,000 and was asked to confirm a figure they never gave. Agreeing would have set the wrong field and changed their verdict. Extraction now receives the field that was asked. | 2026-08-31 |
| OI-46 | Answering a multiple-choice question with the exact option we offered extracted nothing: the cue lists are substring-matched and a bare "sc" cue would fire inside "school", so no cue existed. A tapped chip in the web app and a numbered reply on WhatsApp both fell through, and the orchestrator re-asked. The session now records the last question and its choices, and an exact match binds directly. | 2026-08-31 |
| OI-47 | uvicorn's access log wrote a second line for every request, duplicating the middleware's and always carrying an empty request_id because it runs outside the ContextVar scope — two lines per request, one of them untraceable. Disabled rather than reformatted. | 2026-08-31 |
| OI-49 | The `PARTNERS_ROUTED` audit row was written by the HTTP route rather than by `routing.find_partners`, so the anti-misrouting KPI counted only decisions that arrived over HTTP. The demo seeder calls the service directly, and the ministry dashboard reported "shown a partner: 0" beside 39 applications. The audit now lives with the decision; the route audits only the cache-hit path it alone can see. | 2026-09-01 |
| OI-50 | `Notification.attempts` has a Python-side column default, which is applied at flush — so `attempts += 1` inside `notify()` raised `NoneType + int`. The fail-open guard caught it and the application transition stood, which is exactly why it went unnoticed: the citizen's message was silently dropped. Found by seeding 39 journeys at once. | 2026-09-01 |
| OI-51 | The WhatsApp simulator seeded `useState` with `Math.random()`. A `"use client"` component is still server-rendered, so the initialiser ran twice with different values and React threw a hydration error in the browser — while `tsc`, ESLint, `next build` and all 46 TypeScript tests passed, because the bug only existed at runtime. The sender is now generated in a `useEffect`, and `check:hydration` fails the build on the whole class, including when the randomness hides behind a helper function. | 2026-09-01 |
| OI-52 | Scheme ranking was a deterministic sort key with no account given to the citizen: they saw a rank and a confidence but no reason scheme A beat scheme B, while partner routing already showed a full component breakdown. Five weighted components now drive the order and are shown in six languages. | 2026-09-01 |
| OI-53 | Python's `round()` is half-to-even and JavaScript's `Math.round` is half-up. The fit score produced an exact halfway case (96.7 x 0.15 scales to 1450.5), so the two engines disagreed — 14.5 against 14.51. Caught by the conformance suite. Rounding is now defined explicitly in both rather than inherited from either language. | 2026-09-01 |
| OI-54 | `make demo` was not idempotent: the reference seeder wholesale-replaced the partner registry, which the demo seeder's applications then referenced, so the second run died on a foreign key. Re-running the seed is the documented way to recover a broken demo, so it had to survive being run twice. The registry is now kept when it is already referenced — the generator is deterministic, so what is there is what would be rebuilt. | 2026-09-01 |
| OI-55 | A NUL byte — legal in JSON as ``, legal in a URL as `%00` — passed Pydantic and the rule engine and died inside asyncpg, because Postgres `text` and `jsonb` cannot store one. A 500 on a public, unauthenticated endpoint, which is an information disclosure whether or not the payload achieved anything. Rejected at the edge with a 400. Found by the security surface tests on their first run. | 2026-09-01 |
| OI-56 | The eligibility p95 requirement was stated and never measured, which is a claim rather than a fact. `scripts/bench.py` measures three layers separately: the engine alone p95 0.23 ms, `/match` over HTTP p95 **9.46 ms** against a 500 ms requirement, PostGIS routing p95 12.52 ms. | 2026-09-02 |
| OI-57 | The citizen app had `http://localhost:8000` baked in as its API fallback, which assumed the browser and the API were the same machine. On a phone `localhost` is the phone, so every call failed — the device this product is designed for was the one device it could not run on, which is why OI-29 stayed open. The base URL now follows `window.location`, and CORS admits private-range origins in development only. | 2026-09-02 |
| OI-58 | The null-byte guard checked the URL path and the request body but not the **query string**. `GET /partners/directory?q=%00x` reached an ILIKE and died inside asyncpg — the same 500-on-a-public-endpoint as OI-55, through the one door that pass left open. Found the first time the new directory endpoint was fuzzed, which is the argument for extending the security surface tests alongside every new public route. | 2026-09-04 |
| OI-59 | Three security-surface tests asserted a specific 422 and failed **only when the file was run whole**, because the suite's own several-hundred requests exhausted the shared rate-limit bucket and the API correctly answered 429. A flake that looks exactly like a regression. Those assertions now go through `_refused_with`, which skips on 429 rather than pretending validation broke. | 2026-09-04 |
| OI-60 | `redirect_suggestion` reached the citizen as a raw internal code again — the new match card rendered "instead see NSFDC_TERM_LOAN" in all six languages. OI-25 fixed this on the explanation path only; the field itself still carries a code, and the new UI read it directly. Caught by looking at the Tamil screenshot, not by any check. Resolved in the UI against the run's own results, which already carry every scheme's official name. | 2026-09-04 |
| OI-61 | Adding `users.citizen_id` made `make demo` destroy every login. `demo.py`'s reset used `TRUNCATE ... CASCADE`, whose CASCADE is **schema-level** — it truncates any table holding a foreign key to a named one, whether or not a row points there — so it followed the new key into `users` and emptied it. Both consoles and the judge console stopped working; the seeder printed success and nothing reported an error. Nulling the column first does not help. Now ordered `DELETE`s, with the citizen login detached and re-attached to a fresh consent record through the normal signup path, and a test that parses `reset()` and fails if TRUNCATE returns. | 2026-09-04 |
