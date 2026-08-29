# Translations

Every language a citizen can be answered in, one file per language.

## Why these live here and not in the scheme files

`schemes/*.yaml` carries `en` and `hi` inline, because those are the **reviewed**
languages and they belong next to the rules they describe. Everything else lives here so
that:

- adding a language is a file, not a code change in six places
- a translator sees only strings, never rule syntax they could break
- each language declares its own review status in one obvious place

## Status is not decoration

```yaml
status: draft        # draft | verified
reviewed_by: null
reviewed_on: null
```

**`draft` means written by a language model and never read by a native speaker.** These
strings tell a citizen why they were refused government credit. A mistranslation is not
a cosmetic bug.

`status` travels all the way out: every `MatchResult` carries `translation_status`, so a
UI can badge unreviewed copy and a reviewer can see at a glance what is trustworthy.

| Language | Status |
|---|---|
| `en` English | **verified** — inline in the scheme files |
| `hi` हिन्दी | **verified** — inline in the scheme files |
| `mr` मराठी | draft |
| `bn` বাংলা | draft |
| `ta` தமிழ் | draft |
| `te` తెలుగు | draft |

## Promoting a language to verified

1. A fluent speaker reads every string in the file — `rules`, `fields`, `ui`.
2. Check the amounts. `Rs 5,00,000` and `Rs 1,40,000` appear in prose and must stay
   correct and in Indian digit grouping.
3. Check nothing promises money. `approval_claims` lists words that assert a decision
   this service never makes; the reviewer should add any the list has missed in their
   language.
4. Set `status: verified`, fill `reviewed_by` and `reviewed_on`.
5. Run `pytest packages/rules apps/api` — a test asserts the language's own templates do
   not trip its own approval blocklist.

## What each section is for

| Key | Used by |
|---|---|
| `rules` | Eligibility reasons — `matched_because` / `blocked_because` |
| `fields` | The adaptive questionnaire's question text |
| `ui` | Explanation templates, the amount sentence, confirmation prompts |
| `approval_claims` | Backstop that discards model prose claiming a sanction |
| `cues` | Extra keyword vocabulary for deterministic extraction |

`cues` is additive: English and romanised-Hindi cues always apply too, because a citizen
may type either while asking for answers in Tamil.

## What is deliberately never translated

**Official scheme names.** `Micro Finance Scheme`, `Term Loan` and
`Educational Loan Scheme` are legal names and appear in Latin script in every language.
A live model once rendered "मिनी फाइनेंस स्कीम" for the Micro Finance Scheme; explanations
that do not preserve the official name are now discarded. See CLAUDE.md.

**Rupee amounts.** Rendered by `amount_sentence()` from the `ui.amount` template, never
written by a model.
