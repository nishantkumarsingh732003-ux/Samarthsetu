# Open items

Known gaps, blockers, and deliberate omissions. Every entry says what is missing, why
it is missing, who can close it, and what breaks if it stays open.

Nothing here is a surprise on demo day if it is read first.

**Legend** — 🔴 blocks the demo · 🟡 weakens the demo · 🟢 tracked, not urgent

Last reviewed: 2026-08-29 (after Phase 1)

---

## 🔴 OI-1 — `docker compose up` has never been run

**Status:** open · **Owner:** repo owner · **Since:** Phase 0

Docker is not installed on the development machine (`docker.exe` not on PATH, no
`C:\Program Files\Docker`). Phase 0's headline acceptance criterion — *"`docker compose
up` from a clean clone gives a healthy API at /health and a Next.js page at /"* — is
therefore **unverified**.

What *is* verified without Docker: the migration renders correct PostgreSQL DDL
(`alembic upgrade head --sql`), the schema tests run with no database, the API serves
`/health` under uvicorn, and the web app builds.

What is **not** verified: the compose file itself, the custom PostGIS + pgvector image
(`infra/docker/postgres/Dockerfile`), the entrypoint's wait-then-migrate sequence, and
whether `postgresql-16-pgvector` is actually installable on the `postgis/postgis:16-3.4`
base.

**To close:**
```powershell
winget install Docker.DockerDesktop     # needs WSL2 and a reboot
docker compose up                        # then confirm /health and http://localhost:3000
```

**If it stays open:** the demo cannot be run from a clean clone, which is the single
thing the acceptance criteria are built around.

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

**Status:** open · **Owner:** Phase 2 · **Since:** Phase 1

`packages/rules` is installable (`pip install -e packages/rules`) and importable, but
no API endpoint calls it and no `match_runs` row is written yet. Phase 2 adds
`POST /api/v1/match`.

The Docker path also needs attention: `apps/api/Dockerfile` only copies `apps/api`, so
the rules package must be installed into the image or added to `PYTHONPATH` via the
existing `./packages/rules:/packages/rules` mount.

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
