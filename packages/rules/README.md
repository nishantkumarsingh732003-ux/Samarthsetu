# `packages/rules` — the deterministic eligibility engine

**No language model participates in any decision made here.** Given the same profile and
the same rule files, this package returns byte-identical output every time. That is what
makes a verdict replayable from a `match_runs` row months after the fact.

An LLM may extract facts into a profile *before* this runs, and may restate the reasons
this returns *after* it runs. It never sees a verdict before the engine decides it, and
it cannot change one.

## Layout

| Path | What it is |
|---|---|
| `schemes/*.yaml` | The rules. Data, not code — a policy change is a YAML edit. |
| `src/setu_rules/` | Python reference implementation (used by `apps/api`). |
| `ts/src/` | TypeScript port (used by `apps/web` for in-browser previews). |
| `dist/rules.json` | Compiled bundle: expression ASTs + field contract. Generated. |
| `tests/golden/expected.json` | Snapshot of every verdict. Generated. Diff it in review. |

## How the two runtimes are kept from drifting

Python parses and validates the DSL, then compiles each `when:` expression into a small
JSON tree. TypeScript never parses the DSL — it interprets that same compiled tree from
`dist/rules.json`. The field contract (question text, tie-break priorities) ships in the
same bundle.

`ts/test/conformance.test.ts` runs the TypeScript engine against the *Python-generated*
golden file. If the browser and the API would ever give a citizen different answers, CI
fails.

```bash
pytest packages/rules -q          # 90 tests, Python engine
pnpm --filter @setu/rules test    # 19 tests, incl. 12 conformance cases
```

## Three-valued logic is the point

A comparison against a field the citizen has not supplied evaluates to `UNKNOWN`, never
to `False`:

```python
evaluate({"annual_family_income": None})   # -> NEED_MORE_INFO, not INELIGIBLE
```

A half-finished form must never read as "you do not qualify". `UNKNOWN` deliberately
raises on `bool()` so no `if value:` can silently collapse it to false.

## Verdicts

| | When |
|---|---|
| `INELIGIBLE` | A `HARD_BLOCK` rule is definitively true |
| `NEED_MORE_INFO` | No block fired, but a `HARD_BLOCK` rule references a field we do not have |
| `LIKELY_ELIGIBLE` | All blocks pass, a `SOFT_WARN` fired |
| `ELIGIBLE` | All blocks pass, nothing warned |

## `next_best_question` — ask only what can change the answer

Scores every unsupplied field by how many currently-undecided `HARD_BLOCK` rules it
would resolve, across all schemes. Highest wins; ties break on declared priority, then
alphabetically, so it is a pure function.

Two behaviours worth knowing:

- A scheme with even one definite block is **settled**. None of its other unknown rules
  generate questions. A student is never asked to confirm an admission for a scheme
  their income already ruled out.
- Fields no rule references are never asked. `education_level`, `gender`, and `is_pwd`
  are in the profile contract but cannot currently move any verdict, so the
  questionnaire skips them.

## Rule authoring

Rules evaluate **in file order**, and the first blocking rule with a `suggest_instead`
supplies the redirect. Order therefore decides where a citizen gets sent:

```yaml
- id: MF_NOT_FOR_EDUCATION      # purpose first...
  suggest_instead: NSFDC_EDUCATION_LOAN
- id: MF_PROJECT_COST_BAND      # ...then size
  suggest_instead: NSFDC_TERM_LOAN
```

Reversed, a student asking for Rs 6,00,000 gets pointed at a Term Loan they cannot
use — exactly the misrouting this project exists to prevent. `test_engine.py` pins it.

Expressions are parsed with a whitelisted AST walker: no `eval`, no calls, no
subscripts, no attribute access beyond `profile.<field>`, and every field name is
checked against the contract at load time. Literals follow YAML (`true`/`false`/`null`).

## Changing the rules

```bash
# 1. edit packages/rules/schemes/*.yaml
make rules                       # recompile bundle + golden snapshot
# 2. read the golden diff — it shows which citizens' verdicts moved
# 3. bump ENGINE_VERSION and PINNED_RULES_DIGEST in src/setu_rules/version.py
pytest packages/rules -q
```

Step 3 is enforced. `test_versioning.py` pins the content hash of `schemes/`, so CI
fails until the version and digest are updated together. Eligibility policy cannot
change quietly, and no code deploy is required to change it.

## Two ceilings, never one

NSFDC states an eligibility **band** on what the unit or course may cost, and separately
a cap on the **loan** it will advance. These are different numbers and conflating them
overstates what a citizen can borrow:

| | Project-cost band | Loan cap |
|---|---|---|
| Micro Finance | up to Rs 1,40,000 | Rs 1,25,000 |
| Term Loan | over Rs 1,40,000, up to Rs 50,00,000 | Rs 45,00,000 |
| Educational Loan | not stated | Rs 40,00,000 |

The problem statement quotes only the band. 90% of a Rs 1,40,000 micro-finance project
is Rs 1,26,000 — above the Rs 1,25,000 loan cap. `indicative_amount` therefore uses
`max_loan_amount`, ranking uses `max_project_cost`, and a `SOFT_WARN` fires from
Rs 1,38,889 upward telling the citizen they must fund the difference themselves.

## Provenance status — read before quoting any number

Amounts, interest rates, tenure, and moratorium are verified against
[nsfdc.nic.in/scheme](https://nsfdc.nic.in/scheme) as of **2026-08-29**. The
Rs 5,00,000 income ceiling comes from
[nsfdc.nic.in/eligibility-requirements](https://nsfdc.nic.in/eligibility-requirements),
which states it as effective 2026-01-07.

No scheme **circular number** has been located, so `circular_ref` and `effective_from`
remain null and all three schemes keep `needs_verification: true`.

Figures with no single sourced value are `null`, not invented, and each is recorded as
a `provenance.open_questions` entry:

- The Educational Loan Scheme has **no project-cost band** and therefore no band rule.
- Its `tenure_months` is null — NSFDC states 12 years *or* 10 years depending on
  disbursement status — and its `moratorium_months` is null, being "course period plus
  one year".
- The Term Loan's 12-month plantation/construction moratorium is not modelled; the
  profile holds no activity-type field.

`test_versioning.py` enforces all of this: every scheme must cite an `https://`
`source_url`, must declare at least one open question, and interest rates must sit
inside the problem statement's 6.5–8.0% band.

## Translation status

`en` and `hi` are complete for every rule. `mr`, `bn`, `ta`, and `te` are listed in each
file's `pending_translations` and fall back to English at runtime — deliberately absent
rather than machine-translated, since a wrong reason in Tamil is worse than a correct
one in English. `test_versioning.py` enforces en/hi completeness.
