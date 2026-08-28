# Reference material (NOT authoritative)

Everything in this folder is carried over from the pre-CLAUDE.md scaffold. It is kept
as *input* for the Phase 1 rule authoring, not as a source of truth.

**Read this before copying any number out of these files.**

| File | What it is | Why it is not authoritative |
|---|---|---|
| `schemes.sample.json` | Early sketch of the three scheme families | Carries figures with no `source_url` — e.g. Micro Finance at 6.0% p.a. (the problem statement says the concessional band is 6.5–8.0%) and an Educational Loan ceiling of Rs 30,00,000 that appears nowhere in the problem statement. Both violate CLAUDE.md rule 2. |
| `partners.sample.json` | Shape sketch for the partner registry | Synthetic. Phase 2 generates the real seed set. |
| `geo-README.md` | Notes on geo data sources | Informational. |

Phase 1 authors `packages/rules/schemes/*.yaml` using **only** figures stated in the
problem statement, with `source_url` / `circular_ref` / `effective_from` /
`last_verified_on` on every scheme, and `needs_verification: true` wherever the
problem statement is silent.
