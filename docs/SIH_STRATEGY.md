# SamarthSetu — SIH competition strategy

How to win the room, in the order the room decides.

A jury forms a view in the first two minutes, experiences the product in five, and spends
the remaining ten deciding whether to believe it. Everything below is organised around
that sequence.

---

## The one sentence

> **AI understands the citizen. Rules decide eligibility. Data routes the citizen.
> Evidence explains the decision.**

Say it in the first thirty seconds. Every later claim is evidence for it.

## The one number

> **2,216 wrong-counter outcomes prevented across 39 citizens.**

Not "AI-powered". Not "94% accuracy". A count of the specific harm the problem statement
names, measured by the system itself and queryable live.

---

## What actually separates this from the other entries

Most entries for this problem statement will be a chatbot over a scheme list. Expect
three or four to be genuinely good. The differentiators below are the ones a jury can
verify in the room, ranked by how hard they are to fake.

### 1. The LLM never decides — and we prove it live

Every team will *say* their AI is reliable. We take the model away and the verdict does
not move.

```
make chaos
✓ Same scheme matched     ✓ Same verdict     ✓ Same rules fired, in the same order
✓ Same rules digest — policy did not shift
PASS — the core service degrades, it does not die.
```

The rules digest coming back **byte-identical** is the argument. Not a slide.

**If a judge asks one question, it will be this one.** The answer is: eligibility is a
deterministic, versioned rule engine; the model reads messy words and restates reasons;
every decision carries an engine version, a rules digest and the rule IDs that fired; and
`match_runs` is never deleted, so a sanction is replayable against the rules that were
live when the citizen applied.

### 2. "Nearby, but cannot help"

The single clearest visual proof that we solved the *stated* problem — misrouting — and
not "build a chatbot for schemes".

> *Bank of Maharashtra, Nagpur — is 4.2 km away but is not authorised for the Micro
> Finance Scheme.*

Every excluded branch names the rule that excluded it. Nobody else will have this screen,
because it only exists if you modelled the authorisation matrix rather than the scheme
list.

### 3. Ramesh, and the redirect

He asks about the scheme everyone has heard of with a ₹12 lakh project. The engine tells
him it does not fit **and names the Term Loan instead** — before he goes anywhere.

This is the problem statement's own words ("confusion between schemes") answered on
screen in four seconds.

### 4. Underserved districts

The insight the ministry does not currently have. Demand measured from **eligibility
checks, not applications** — because the citizens who matter most looked, found nothing,
and never appear in an application table.

> Lucknow: 7 partners, and **not one** can process an Educational Loan.

Frame it as a procurement instrument, not a chart. This is the slide a ministry official
remembers.

### 5. The redaction proof

Not "we take privacy seriously". A test that renders an Aadhaar card, confirms OCR can
read it, runs the pipeline, and OCRs the *stored pixels* to prove the digits are gone.

Run it if a judge is technical. It takes four seconds.

---

## Demo order, and why

`docs/DEMO_SCRIPT.md` has the exact clicks. The *order* is strategic:

| Time | Beat | Why here |
|---|---|---|
| 0:00 | Problem + the one number | Anchors before any screen |
| 0:30 | The governance claim, stated | Frames everything after it as evidence |
| 1:00 | Sunita — match, with rule IDs | The happy path, and explainability |
| 2:00 | "Nearby, but cannot help" | The differentiator, while attention is highest |
| 3:00 | Ramesh — the redirect | The problem statement's own words |
| 3:45 | Partner console + live capacity toggle | Proves it is a system, not a screen |
| 4:45 | Ministry dashboard | The policy insight |
| 5:30 | WhatsApp, then `make chaos` | Reach, then the proof, as the last thing they see |

**Never open with the chatbot.** Every other team opens with the chatbot.

**End on `make chaos`.** Working software under failure conditions reads as engineering
maturity, and it is the last thing in their memory when they score.

---

## Handling the hard questions

| Question | Answer |
|---|---|
| "Is the partner data real?" | No. 120 synthetic partners pending the official MoSJE master, disclosed in the README and on the routing screen. Scheme figures are verified against nsfdc.nic.in; no circular number yet, tracked as OI-3 |
| "What happens when the rules change next April?" | Edit the YAML, bump `engine_version`, re-run the golden tests. No code deploy. Past decisions stay replayable because each application snapshots its `match_run_id` and engine version |
| "How do you know the AI isn't hallucinating eligibility?" | It is never asked. The verdict is computed before the model is consulted, and the model is never handed the rupee figure. 36 tests, plus `make chaos` |
| "Does it approve loans?" | No, and every screen says so. SamarthSetu matches and routes; a Channel Partner decides |
| "Is it accessible?" | WCAG AA on every palette pair as a build gate, 100/100/100/100 Lighthouse, 114 KB of a 200 KB budget, works offline. Not yet walked on a real low-end handset — OI-29 |
| "What's not finished?" | Hand them `docs/OPEN_ITEMS.md`. 51 entries, open ones first |

**On that last one:** volunteer the open items before they find them. A team that says
"notifications cannot actually leave the building because we deliberately do not store a
dialable number" reads as more trustworthy than one that has no known gaps.

---

## What we deliberately did not build, and why it helps

Say this if asked why there is no agent framework:

- **No autonomous agents / multi-agent orchestration.** Nothing in the journey needs
  planning. A rule engine and a router are the correct shapes.
- **No blockchain.** There is no multi-party trust problem here that an append-only audit
  table does not solve.
- **No opaque ML scoring.** A citizen refused by a model they cannot interrogate is the
  problem, not the solution.
- **No fake government API.** Where data is synthetic it is labelled.

Restraint is a technical argument. Make it one.

---

## Risks, and the mitigation on the day

| Risk | Mitigation |
|---|---|
| Wi-fi fails | Everything runs on `docker compose up`. No external API in the demo path |
| The LLM key is dead | `LLM_PROVIDER=none` is fully supported. This is a feature we demo on purpose |
| A screen is empty | `make demo` rebuilds the world in ~2 seconds |
| Someone else demos first and looks similar | Lead with `why_not[]` and the chaos drill. Neither can be assembled the night before |
| A judge asks for the code | `packages/rules/schemes/*.yaml` — a non-programmer can read a rule with its source URL |
| Time overrun | Cut in this order: WhatsApp, then the partner console, then the funnel. **Never cut** the redirect, `why_not[]`, or the chaos drill |

---

## Scoring rubric, and where we sit

| Typical criterion | Our evidence |
|---|---|
| Problem understanding | Both halves of PS 26092 answered, including the routing half most teams miss |
| Innovation | Determinism as the feature, not the AI. `why_not[]`. Underserved districts |
| Technical depth | PostGIS, Kleene logic, AST evaluator, dual engine with conformance tests, 501 tests |
| Practicality | Runs in 40 s from a clean clone; SSO and partner-master seams named |
| Scalability | Stateless API, indexed geo queries, cacheable pure engine, scheme count is data |
| UI/UX | Six languages, WCAG AA gated, 114 KB, offline, feature-phone channel |
| Impact | Misrouting prevented, and a procurement instrument for the ministry |

**The weakest column is field validation** — synthetic partners, unverified circulars, no
real-handset test. Say it before they ask, and say what would close it.
