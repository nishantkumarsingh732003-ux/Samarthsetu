# API v1

Base: `/api/v1`. Interactive spec at `/docs`; the machine-readable source is
`/openapi.json`, which is generated from the route definitions and is the thing to
believe if this file and the service ever disagree.

> This page replaced a Phase-0 sketch that had drifted a long way from the code — it
> described OTP auth, a `/profiles` resource, `/match/explain` and `/assistant/chat`,
> none of which exist. Regenerate it from `/openapi.json` rather than editing it by hand
> when routes change:
>
> ```bash
> python - <<'PY'
> import httpx
> spec = httpx.get("http://localhost:8000/openapi.json").json()
> for path, ops in sorted(spec["paths"].items()):
>     for method, op in ops.items():
>         print(f"{method.upper():6} {path:46} {op.get('summary', '')}")
> PY
> ```

## What needs a login, and what deliberately does not

The citizen journey works **signed out, end to end**: check eligibility, find the
authorised partner, submit an application, and track it by its reference number. That is
the design, not an omission — requiring an account to find out which scheme fits you is
the barrier this project exists to remove.

| Group | Auth |
|---|---|
| Matching, conversation, schemes, partners, applications, documents, webhook | **None** |
| `/citizen/*` | Bearer token, role `CITIZEN` |
| `/partner/*` | Bearer token, role `PARTNER`, scoped to one Channel Partner |
| `/admin/*` | Bearer token, role `ADMIN` |

Roles do not nest. An admin token gets 403 from `/citizen/me` and from `/partner/queue`,
not a fallthrough. Partner-side scoping is a `WHERE` clause inside every query rather
than a check beside it, so a forgotten guard returns nothing instead of widening the
result set.

## Matching — the deterministic engine

| Method | Path | Purpose |
|---|---|---|
| POST | `/match` | Profile in → every scheme with a verdict, reasons and rule ids |

No language model participates in a verdict. Missing facts produce `NEED_MORE_INFO` plus
the single next question worth asking, never a refusal. Every call writes a `match_runs`
row and an audit entry, so a verdict shown to a citizen can be reproduced from storage.

## Schemes — the published catalogue

| Method | Path | Purpose |
|---|---|---|
| GET | `/schemes` | Every scheme in the rule pack, with limits, provenance and partner counts |
| GET | `/schemes/{code}` | One scheme: every rule expression verbatim, documents, sources |

Served from the versioned rule pack rather than from the `schemes` table, because the
YAML carries the provenance — including the **open questions** against figures that could
not be sourced — and the table is a projection that would drop them. Unauthenticated: a
citizen should be able to read the published terms before handing over any data.

## Channel partners

| Method | Path | Purpose |
|---|---|---|
| POST | `/partners/route` | **The recommendation.** Ranks authorised partners on distance, ticket size and load, with a score breakdown |
| GET | `/partners/coverage` | Coverage by state — distinct partner counts and the type mix |
| GET | `/partners/coverage/{state}` | Districts within a state; a district with no SCA is the finding |
| GET | `/partners/directory` | Flat, unranked list behind a map or a search box |
| GET | `/partners/{partner_id}` | One partner and its full authorisation matrix |

Only `/route` ranks. The other three are deliberately unranked: a directory sorted by
anything starts being read as advice, and advice about where to take a loan application
has to come from the surface that can explain its reasoning.

Route ordering matters here — `/partners/coverage` and `/partners/directory` are
registered *before* `/partners/{partner_id}`, which would otherwise swallow them as
malformed UUIDs.

## Conversation

| Method | Path | Purpose |
|---|---|---|
| POST | `/conversation/turn` | One turn: extract facts, run the engine, ask the next question |
| GET/POST | `/webhook/whatsapp` | The same orchestrator over a text-only channel |

The model extracts structured facts from messy input and restates the engine's reasons in
the citizen's language. It never decides.

## Applications and documents

| Method | Path | Purpose |
|---|---|---|
| POST | `/applications` | Submit to a Channel Partner; returns a quotable reference number |
| GET | `/applications/{reference_no}` | Tracking view — timeline, documents, what is outstanding |
| POST | `/applications/{reference_no}/documents` | Upload; government IDs are masked before storage |
| POST | `/applications/{reference_no}/transition` | Advance the lifecycle (partner-side) |
| GET | `/documents/checklist` | What to bring, before an application exists |

An application snapshots `match_run_id` and `engine_version`, so a sanction can be
replayed against the rules that were live when the citizen applied.

## Sign-in

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Email and password, any role; returns a bearer token |
| GET | `/auth/me` | Who the current token belongs to |

One password path for every role — the seam where NIC / Parichay SSO replaces this.
Metered hardest of any endpoint, because it is the only one worth brute-forcing, and it
returns the same message for a wrong address and a wrong password so the response is not
an oracle for which addresses are registered.

## Citizen account — optional, and only persistence

| Method | Path | Purpose |
|---|---|---|
| POST | `/citizen/signup` | Create an account. Refused without explicit consent |
| GET | `/citizen/me` | The signed-in citizen and their stored profile |
| PUT | `/citizen/profile` | Partial update; absent keys are left alone, an explicit null clears |
| POST | `/citizen/profile/demo` | Fill the profile with the demo persona |
| GET | `/citizen/matches` | The stored profile through the same engine as `POST /match` |
| GET | `/citizen/applications` | This citizen's own applications, newest first |

Three properties worth stating, each with a test behind it:

- **No privilege.** `GET /citizen/matches` and `POST /match` return identical verdicts for
  identical facts. Asserted over the wire in `test_security_surface.py`.
- **Consent first.** Signup writes a `consents` row before the `citizens` row, because
  `citizens.consent_id` is `NOT NULL`. A signup that skipped consent is refused by the
  database, not by a code review.
- **A wall to the engine.** The profile stores things the rules must never read — a
  business name, a description, the amount the applicant *says* they need.
  `engine_profile()` projects it down to `setu_rules.profile.FIELDS` and nothing else, and
  the response returns that projection so it can be inspected rather than trusted.

## Meta

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | The process is up |
| GET | `/readyz` | What it can currently reach — and whether eligibility still works |

`/readyz` reports the model provider as *configuration*, not reachability, and states
`llm_required_for_eligibility: false`. A service that still decides eligibility correctly
with the model offline is healthy, and taking it out of rotation for that would be the bug.

## Errors

Every response carries `X-Request-ID`, and every error body repeats it as `request_id`, so
a citizen quoting a reference off an error screen gives support one thing to grep.

| Status | Meaning here |
|---|---|
| 400 | Malformed at the edge — a NUL byte in the path, query or body; consent withheld |
| 401 | No token, or one that is expired, forged or unsigned |
| 403 | Authenticated, wrong role |
| 404 | Unknown scheme, partner, reference or state. Worded identically whether or not the thing exists |
| 409 | That email already has an account |
| 422 | Failed validation — an unknown profile field, an out-of-range coordinate, an unsupported language |
| 429 | Rate limited. Carries `Retry-After` |

No error returns a traceback, a table name or a library version. `tests/test_security_surface.py`
asserts that against every public endpoint with injection-shaped, oversized and malformed input.
