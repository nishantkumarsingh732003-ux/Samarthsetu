# SETU — six-minute demo run sheet

Exact clicks, and the sentence to say at each one. Timings are cumulative.

**Before you start**

```bash
docker compose up -d
make demo                     # reference data, then the demo world
```

Open four tabs and leave them on these pages:

| Tab | URL |
|---|---|
| 0 | http://localhost:3000/demo ← **the console; drive from here if anything goes wrong** |
| 1 | http://localhost:3000 |
| 2 | http://localhost:3000/console/login |
| 3 | http://localhost:3000/demo/whatsapp |
| 4 | a terminal in the repo root |

Sign tab 2 in as `admin@setu.gov.in` / `setu-demo-2026` and leave it on `/console/admin`.
Have a second browser profile signed in as `partner@setu.gov.in` if you want the partner
console without signing out mid-demo.

> The single most important thing you say is in the first thirty seconds, and it is
> **"the language model never decides eligibility."** Everything else is evidence for it.

---

## 0:00 — The problem, in one sentence and one number

**Say:** *"A Scheduled Caste entrepreneur cannot answer two questions: which scheme fits
me, and which of the hundred-plus Channel Partners near me is authorised to process that
specific scheme. So they guess, they walk into the wrong branch, and the application is
misrouted. In our seeded world, the router prevented **2,216 wrong-counter outcomes**
across 39 citizens."*

Do not open anything yet. Let the number sit.

---

## 0:30 — The governance claim, stated before anything is shown

**Say:** *"Before I show you a single screen: eligibility here is decided by a
deterministic, versioned rule engine. A language model reads the citizen's messy words
and restates the answer in their language. It never participates in the verdict. Every
decision carries an engine version, a rules digest, and the exact rule IDs that fired."*

**Say:** *"I will prove that at the end by taking the model away entirely."*

---

## 1:00 — Sunita, on tab 1

**Click:** the language picker → **हिन्दी** → **मेरी योजना खोजें**.

**Type or say:** `mujhe sabzi ka thela lagana hai`

**Say:** *"She is typing Hinglish into a Rs 6,000 phone. She does not know the word
'scheme', and she should not have to."*

Answer the questions as they come — `80 hazaar`, tap **SC**, `1.8 lakh`.

**On the results screen, click "Why this scheme?"**

**Say:** *"Every reason has a rule ID. `MF_INCOME_CEILING` is not a sentence a model
wrote — it is a rule in a YAML file with a source URL and a last-verified date. If the
ministry changes the income ceiling next April, we edit YAML, bump the engine version,
re-run the golden tests. No code deploy."*

---

## 2:00 — The screen that proves we solved the *stated* problem

**Click:** **मेरे पास कार्यालय खोजें** (find an office near me).

Point at the ranked list, then scroll to **"Nearby, but cannot help"**.

**Say:** *"This is the whole problem statement on one screen. These branches are close to
Sunita. Each one has the exact rule that excludes it — not authorised for this scheme,
paused for capacity, beyond the service radius. She would have walked into one of these.
Now she doesn't."*

**Click:** "Why this order?" on the top partner.

**Say:** *"And the ranking is not a black box either — distance, speed, capacity,
suitability, each shown separately. She can see that a closer branch lost because it was
busy."*

---

## 3:00 — Ramesh, and the redirect

Back to tab 1, start again. **Type:** `mujhe furniture ka workshop lagana hai, 12 lakh chahiye`

**Say:** *"Ramesh asked about the scheme everyone has heard of. Twelve lakh is far above
the Micro Finance ceiling — so the engine tells him **it does not fit, and names the one
that does**. He is redirected to the Term Loan before he goes anywhere near a branch."*

Point at the greyed Micro Finance card with `MF_PROJECT_COST_BAND` and its
"Consider instead" line.

**Say:** *"We show the refusal rather than hiding it. A citizen who is told nothing
assumes we simply failed to consider it."*

---

## 3:45 — The partner console

Switch to the partner browser profile → `/console/partner`.

**Say:** *"Same application, from the branch officer's side."*

Point at one queue row.

**Say:** *"Readiness with the missing documents **named**, an SLA clock against this
branch's own stated turnaround, and — " (click **Why was this routed here?**) " — the
rule IDs that sent it here. An officer who can see why a case landed on their desk can
push back when it shouldn't have."*

**Then, the live moment.** Scroll to **Intake capacity** → toggle **Micro Finance Scheme**
to **Paused**.

Switch to tab 1, redo Sunita's partner search.

**Say:** *"That branch is gone from her list — and she is told exactly why, in her own
language. The console writes to the same table the routing engine filters on."*

Toggle it back on.

---

## 4:45 — The ministry dashboard

Tab 2, `/console/admin`.

**Say:** *"Three roles, three genuinely different experiences, one login. This is the
Ministry view, and every figure is a live query — no fixture, no cached snapshot."*

Point at **Misrouting prevented**.

**Say:** *"This is the KPI we would ask to be measured on. Broken down by the rule that
excluded each branch, because 'not authorised for this scheme' and 'too far' are
different policy problems."*

Scroll to **Underserved districts**.

**Say:** *"And this is the thing the ministry does not currently have. These are districts
where citizens ran an eligibility check and no authorised, accepting partner can process
what they matched. Demand is measured from **eligibility checks, not applications** —
because the citizens who matter most are the ones who looked, found nothing, and never
applied at all. Every one of these is unserved for Educational Loans specifically. That is
a procurement decision, not a chart."*

---

## 5:30 — Reach, and then failure

Tab 3, `/demo/whatsapp`. Click **Start the demo**, then answer with `80 hazaar`, `1`,
`1.8 lakh`.

**Say:** *"Same rule engine, same six languages, no smartphone. Four keypad messages to a
verdict. The people furthest from a branch are the least likely to own an Android phone,
and a service that only reaches people who do has selected against exactly the citizens it
was funded to help."*

Point at the segment counter.

**Say:** *"And that counts what it would cost. Indic scripts encode as UCS-2 — seventy
characters a segment instead of a hundred and sixty. Answering someone in Tamil costs
three times an English message, and we made that visible where the copy is written."*

**Tab 4, the last thing you do:**

```bash
make chaos
```

**Say, while it runs:** *"I said the model never decides. This points the running service
at a model endpoint that does not exist and drives a complete citizen journey through the
real API."*

When it prints:

**Say:** *"Same scheme, same verdict, same rules in the same order, **same rules digest**.
Byte-identical — because no model was ever involved in deciding. The core service degrades.
It does not die."*

---

## Questions you will be asked, and the honest answers

**"Is the partner data real?"**
No. The 120 Channel Partners are synthetic, pending the official MoSJE partner master, and
that is stated in the README and on the routing screen itself. The *scheme* figures are
verified against nsfdc.nic.in, though no circular number is cited yet — that is open item
OI-3.

**"What happens when the rules change next April?"**
Edit the YAML, bump `engine_version`, re-run the golden tests. No code deploy. Every past
decision stays replayable against the rules that were live when it was made, because each
application snapshots its `match_run_id` and engine version.

**"Can you prove the Aadhaar redaction?"**
`docker compose exec api python -m pytest tests/test_redaction.py -v` — 18 tests. One of
them renders an Aadhaar-like card, confirms OCR can read the number, runs the real upload
pipeline, then OCRs the *stored bytes* to prove the digits are gone from the pixels.

**"Does it approve loans?"**
No, and it says so on every screen. SETU matches and routes. A Channel Partner decides.

**"What is not finished?"**
`docs/OPEN_ITEMS.md`, 47 entries, open ones first. The two we would fix next: notifications
cannot actually leave the building because we deliberately do not store a dialable number
(OI-43), and the staff console chrome is English-only (OI-35).

---

## If something breaks mid-demo

| Symptom | Do this |
|---|---|
| A screen is empty | `make demo` — rebuilds the world in ~2 seconds |
| API not responding | `docker compose restart api`, wait for `curl localhost:8000/health` |
| Chaos drill left the model down | `docker compose up -d --force-recreate api` |
| Everything is wrong | `docker compose down -v && docker compose up -d && make demo` (~40s) |
