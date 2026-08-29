# Open items

Known gaps, blockers, and deliberate omissions. Every entry says what is missing, why
it is missing, who can close it, and what breaks if it stays open.

Nothing here is a surprise on demo day if it is read first.

**Legend** — 🔴 blocks the demo · 🟡 weakens the demo · 🟢 tracked, not urgent

Last reviewed: 2026-08-29 (after Phase 3)

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

**Status:** open · **Owner:** needs a human translator · **Since:** Phase 1

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

## 🟡 OI-19 — the LLM path has never been executed

**Status:** open · **Owner:** needs an API key · **Since:** Phase 3

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

**Status:** open · **Owner:** Phase 4+ · **Since:** Phase 3

Sector, category, gender and place detection use curated keyword lists covering English,
romanised Hindi and Devanagari. Marathi, Bengali, Tamil and Telugu cue words are absent,
so in those languages extraction currently leans on the numeral parser (which does cover
their digits) plus the LLM path, itself unexercised (OI-19).

Related to OI-4: the same four languages lack rule-message translations.

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
| OI-21 | The orchestrator asked the same question three turns running when a citizen did not answer it. `next_best_question` now takes an `exclude` set, in both the Python and TypeScript engines. | 2026-08-29 |
| OI-16 | Partner service areas were random districts within a state, so a Mumbai branch "served" Nagpur 687km away and the router ranked it. Service areas are now the geographically nearest districts, and routing rejects anything beyond a 150km radius with a stated reason. | 2026-08-29 |
| OI-17 | 120 partners spread uniformly over 53 districts left Nagpur with a single branch, making routing look empty. Seeding now guarantees one partner per district and weights the remainder towards large cities. | 2026-08-29 |
