# SETU — security and privacy model

What the system defends, how, and — as importantly — what it does not defend and why.

> This is a **privacy-preserving, DPDP-aligned design**. It has not been assessed by
> counsel and no compliance claim is made. Where the design follows a specific principle
> of the DPDP Act 2023, the principle is named so a reviewer can check the reasoning
> rather than take the label on trust.

---

## Threat model

| # | Threat | Who | Defence | State |
|---|---|---|---|---|
| T1 | A government ID is stored in full | Us, by accident | Four layers, §1 | mitigated |
| T2 | A citizen's data is read by the wrong partner | Broken authorisation | Query-level scoping, §3 | mitigated |
| T3 | A model fabricates an eligibility decision | LLM | Structural exclusion, §2 | mitigated |
| T4 | An attacker enumerates registered emails | Login timing / message | Constant-time path, §3 | mitigated |
| T5 | An attacker enumerates reference numbers | Tracking endpoint | Identical 404s; **no rate limit on enumeration specifically** | partial |
| T6 | A traceback leaks internals | Unhandled exception | Global error boundary, §4 | mitigated |
| T7 | A runaway script exhausts the service | Any client | Banded rate limiting, fails open, §4 | mitigated |
| T8 | Injection through free text | Citizen or officer input | ORM parameter binding; **no explicit test** | partial |
| T9 | An officer acts without accountability | Insider | Append-only audit log, §5 | mitigated |
| T10 | A stale verdict is served from cache | Us | API never cached client-side | mitigated |

---

## 1. Government identifiers — the four layers

DPDP principle: **data minimisation**. We keep the least that still lets a branch
recognise the right person.

| Layer | Mechanism | Where |
|---|---|---|
| Extracted text | `mask_text` rewrites every ID-shaped run, keeping the last four | `services/redaction.py` |
| Image pixels | `redact_image` paints filled rectangles over the located digits | `services/documents.py` |
| Persistence boundary | `assert_no_government_id` raises rather than writing | `services/redaction.py` |
| Database | `CHECK (gov_id_last4 ~ '^[0-9]{4}$')` and a unique salted hash | `models/citizen.py` |

**What is retained:** the last four digits, plus `sha256(salt || digits)` so a returning
applicant can be recognised without the number ever being held.

**Rotating `ID_HASH_SALT` invalidates every existing hash.** That is correct behaviour,
not a bug: the old hashes stop being meaningful, which is the point of a salt.

**Fails closed.** If OCR is unavailable for an ID-bearing document, or an ID is found in
the text but cannot be located in the pixels, the upload is **refused**. Losing an upload
is recoverable; leaking an Aadhaar number is not.

**The honest limit (OI-32).** A number OCR cannot read is a number we do not know is
there, so nothing is painted and the file is stored as it arrived. That case raises a
`NO_ID_DETECTED` warning to the citizen and the officer rather than being silent. It is
not refused, because refusing would block a citizen whose only camera produces soft
photos from ever supplying a required document. Redaction is therefore **one of four
layers, not the only one** — and it is why the other three exist.

**Proof, not assertion:** `tests/test_redaction.py` renders an Aadhaar-like card,
asserts OCR can read it, runs the real pipeline, then OCRs the *stored bytes*.

## 2. The model cannot decide

DPDP principle adjacent, but mostly administrative-law: a decision affecting a citizen
must be explicable and reproducible.

| Control | Implementation |
|---|---|
| The verdict is computed before the model is consulted | `run_match` completes, then `explain` runs |
| The model never receives the rupee figure | `amount_sentence()` is rendered by us and appended |
| The extraction tool schema offers no money field | `ToolSpec` omits it entirely |
| Prose that renames a scheme is discarded | `_preserves_scheme_name()` |
| Prose implying approval is discarded | `_claims_approval()`, per language |
| Values outside the vocabulary are dropped, not coerced | `_validate_llm_fields()` |
| Uncertain extraction becomes a question | Confidence gate at 0.7 |
| A model outage degrades to templates | `complete_text` returns `None`; never raises |

Every one of these exists because a live model actually did the thing it prevents.

## 3. Authentication and authorisation

**Deliberately minimal**, and the seam is named: production integrates with NIC /
Parichay SSO, and `POST /api/v1/auth/login` is where that swap happens. Nothing else in
the API asks anything but "who is calling".

- bcrypt directly (cost 12). passlib 1.7.4 raises on import against modern bcrypt.
- A password over 72 bytes is **refused, not truncated** — silent truncation means two
  different passwords open one account. Measured in bytes, so 25 Devanagari characters
  is correctly rejected.
- An unknown email is verified against a real generated dummy hash so it costs the same
  ~200 ms as a known one. Without this, response timing enumerates registered addresses.
- Wrong email and wrong password return the **same message**.
- JWT carries the role, but `current_user` re-reads from the database, so deactivating an
  account takes effect immediately. A *role change* waits for token expiry — one hour,
  documented in OI-37 rather than assumed away.
- Login is the hardest-metered endpoint: 10/minute.

**Partner scoping is a `WHERE` clause, not a permission check.** Every partner-side query
filters on the signed-in user's `partner_id`. A forgotten `if` widens a result set
silently; a forgotten join condition returns nothing and is noticed immediately. The
failure mode of the safer shape is a bug you can see. A `CHECK` constraint makes "partner
login with no partner" and "admin scoped to a partner" both unrepresentable.

Another partner's reference number returns **404, not 403** — confirming it exists would
leak that it exists.

## 4. Service integrity

- **Request IDs** in a `ContextVar`, adopted from an upstream proxy, returned in
  `X-Request-ID` and in every error body.
- **Structured JSON logs**, one object per line. The query string is never logged — a
  routing call carries a citizen's coordinates.
- **Rate limiting**, fixed window in Redis, banded: login 10/min, conversation 30/min,
  everything else 120/min. It **fails open** — if Redis is unreachable the request is
  served. Rate limiting exists to stop a runaway script, and a cache outage becoming an
  eligibility outage is the wrong trade for a service people rely on.
- **Global error boundary.** No traceback ever reaches a client; the full detail goes to
  the log with the request ID.
- **No API response is cached client-side.** A stale eligibility verdict is worse than
  none.

## 5. Auditability

Append-only `audit_log`. Never updated, never deleted. Records **who did what, when, to
which entity, and why**.

Audited: every match, every routing decision (including cache hits — a cached decision is
still a decision shown to a citizen), consent, citizen creation, application submission
and every transition, document upload, partner queue reads, capacity changes, analytics
views and exports, login success and failure.

A failed login records **no email address** — a failed login often means someone typed
their password into the email box.

`match_runs` is the reproducibility record and is **never deleted**. `scripts/seed/demo.py`
is the single exception, because a demo reset is not a production operation; that
exception is stated in the module docstring rather than left silent.

## 6. Consent

DPDP principle: **purpose limitation**. A `consents` row is written *before* the citizen
row, and `citizens.consent_id` is `NOT NULL`, so there is no code path that stores
citizen data without a grant to point at. Withholding consent returns 403 and writes
nothing at all — not a consent row, not a citizen row.

This is why notifications cannot yet be delivered by SMS (OI-43): a delivery number needs
its own consent purpose, and adding one silently behind a notification feature would be
exactly the sort of scope creep purpose limitation exists to prevent.

## Known weaknesses

| ID | Weakness | Why it stands |
|---|---|---|
| OI-32 | An unreadable ID is stored unmasked | Refusing would block a citizen with a poor camera. Warned, not silent |
| OI-43 | No dialable number, so SMS cannot send | Deliberate. Lifting it is a consent decision |
| OI-44 | Rate limiting is per-IP; CGNAT makes a town one IP | Limits are set high; failure is a 429, not a lost application |
| T5 | Reference numbers are not enumeration-hardened | The tracking response carries no personal data |
| T8 | No explicit injection test | SQLAlchemy binds parameters throughout; untested is not the same as unhandled |
| OI-48 | Never deployed; `SECRET_KEY` defaults to `change-me` | Checklist in `DEPLOYMENT.md` gates this |
