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

## Provenance status — read before quoting any number

Every figure in `schemes/*.yaml` is transcribed from **SIH 2026 Problem Statement
26092**, not from an NSFDC or MoSJE circular. Consequently every scheme carries
`needs_verification: true`, and `source_url` / `circular_ref` / `effective_from` are
`null` rather than guessed.

Figures the problem statement does **not** state are `null`, not invented:

- The Educational Loan Scheme has **no** `max_amount` and therefore no cost-ceiling rule.
- `tenure_months` and `moratorium_months` are null for all three schemes.

`test_versioning.py` enforces this: a scheme with no `source_url` must declare
`needs_verification` and carry a note saying what to verify.

## Translation status

`en` and `hi` are complete for every rule. `mr`, `bn`, `ta`, and `te` are listed in each
file's `pending_translations` and fall back to English at runtime — deliberately absent
rather than machine-translated, since a wrong reason in Tamil is worse than a correct
one in English. `test_versioning.py` enforces en/hi completeness.
