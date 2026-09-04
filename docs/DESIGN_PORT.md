# Porting the SamarthSetu design drop

A separate front end — 18 pages of Create React App, 48 shadcn/Radix components, about
2,500 lines — was produced on the Emergent preview platform and handed over as the
intended look for this product. This is the record of what was taken from it, what was
not, and why, so nobody has to reconstruct the reasoning from a diff.

Nothing here criticises the drop for being a drop. It is a design artefact and a good
one; it was never a production build and does not claim to be.

## What the drop actually was

| | |
|---|---|
| 18 pages, 48 UI primitives, ~2,500 lines | CRA + CRACO, plain JSX, react-router-dom, recharts, sonner, axios |
| `package.json` | **absent** — nothing could be installed |
| `tailwind.config.js`, `postcss.config.js` | **absent**, though `components.json` referenced the first |
| `node_modules/` | two entries; effectively empty |
| `build/` | empty |
| `craco.config.js` | pointed at `./plugins/health-check/…`; the folder is `./health-check/`. Required `@emergentbase/visual-edits` |
| `.env` | pointed at `sih-setu.preview.emergentagent.com` |

So "adopt it as-is" was never on the table: the build had to be reconstructed from
scratch either way. Given that, the choice was between reconstructing a CRA SPA beside
the existing Next.js app or porting the design into it. CLAUDE.md fixes the stack, and
three of its rules — a <200KB JS budget on the citizen route, offline-first, six
languages — are things a client-only SPA with 90KB of Radix and 95KB of Recharts cannot
meet. The design was ported.

## Adopted

- **The visual language.** Navy `#173B6C`, teal `#0F766E`, saffron as a highlight, a cool
  paper ground, generous rounding, the two dark display panels. The whole app wears it now,
  including the pre-existing anonymous journey — one design system, not two.
- **The information architecture.** Sidebar on a laptop, bottom bar on a phone, and the
  eight destinations the drop identified.
- **Five screens this project did not have**: an EMI planner, scheme comparison, a scheme
  catalogue with detail, a document checklist view, and a profile page.
- **The account model.** A saved profile, saved applications, and onboarding as a wizard.

## Adopted with the numbers fixed

Three palette values failed WCAG AA as drawn and are darkened in `tailwind.config.ts`.
They read fine on a designer's monitor and none of them passes:

| Role | Drop | Here | Why |
|---|---|---|---|
| danger | `#DC2626` | `#B3261E` | 4.02:1 on white, below the 4.5 floor for body text |
| warning | `#D97706` | `#7A4E0A` | 3.18:1 — unreadable as text |
| muted | `#667085` | `#55617A` | 4.29:1, and it is the caption colour used everywhere |

Saffron is not a text colour at any weight — 1.9:1 on white, and no shade of it is both
saffron and legible — so it appears as a background with ink on top, or as a rule.
`scripts/check-contrast.mjs` now asserts 25 pairs and would catch a revert.

## Not adopted, and why

**shadcn / Radix (48 components).** ~90KB gzipped for the handful actually used, against
a 200KB budget for the whole route. The needed primitives are ~200 lines in
`components/ui/`, built on native `<select>`, `<input type="range">` and `<dialog>` —
which are already accessible, already keyboard-navigable and already familiar to a screen
reader. Reimplementing them in divs is how that gets lost.

**Recharts.** ~95KB for one stacked bar chart, which is ~200 lines of SVG instead. The
drop's other three charts were dropped rather than ported: a donut showing a single "92%
match" is a number wearing a costume, and the ministry pies were over categories with no
part-to-whole meaning.

**Google Fonts.** Plus Jakarta Sans, Inter and JetBrains Mono, ~180KB of render-blocking
requests before a citizen on 2G sees a word. The typefaces are *named* in the Tailwind
config so a device that has them uses them; every stack falls back to Noto Sans and then
system-ui. Cost on the wire: zero.

**The invented numbers.** "12,480+ entrepreneurs guided", "42 schemes indexed", "1,240
channel partners". On a page carrying a ministry's name those are not placeholder copy,
they are false claims. CLAUDE.md rule 6 puts the demo path off limits for invented data,
so the landing strip fetches `/schemes` and `/partners/coverage` and shows a dash until
they arrive.

**The document vault.** Five tiles with an upload button that cycled a label between
"Not Uploaded", "Pending" and "Verified" in local state and touched nothing. A fake
"Verified" badge against a caste certificate is the worst possible thing to invent. The
page now shows the real versioned checklist, why each document is asked for, and which
ones contain a government ID that gets masked at ingestion.

**The FAQ tab.** Three invented answers about collateral requirements and processing
times. Made-up policy on a ministry-branded page is worse than a missing tab.

**The scheme names.** The drop listed NBCFDC, Stand-Up India and SIDBI products with
specific rates. This repository's rule pack covers the three NSFDC families the problem
statement actually names, and every figure in it carries a `source_url` and a
`last_verified_on`. Adding schemes means adding sourced YAML, not adding copy.

**The login wall.** The drop routed every call to action to `/auth`. Here the anonymous
journey stays the front door and the account is optional — see
[the account section of the README](../README.md#the-citizen-app).

## Fixed on the way through

- **The moratorium was decorative.** The drop's calculator accepted a moratorium input and
  then ignored it, which understates the total repaid — the direction of error that
  matters. Interest accrues through the holiday and is capitalised; `lib/emi.ts` does that
  and `emi.test.ts` pins it.
- **`emiCalc` divided by zero at 0% interest.** The standard formula has `r` in the
  denominator.
- **The whole profile was posted once, at the end.** Six steps held in memory means a
  citizen who loses signal on step five retypes everything. Each step now saves as it is
  left.
- **The best-match card led with the fit percentage.** That number orders the list; it is
  not the verdict and not a probability of approval. The card leads with the verdict word
  and files the score under "why it ranks here".

## What the port added that the drop did not have

The drilldown from state to district to branch is built on the existing PostGIS registry
rather than the drop's hand-drawn SVG with a `STATE_HOTSPOTS` constant, so it can say the
thing that matters: which districts have banks but no State Channelising Agency, and
therefore cannot process the schemes that route only through one.
