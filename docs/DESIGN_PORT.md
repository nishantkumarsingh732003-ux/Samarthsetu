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


## shadcn, adopted on the second pass

The first pass did not take shadcn: installing the drop's 48 components would have cost
~90KB gzipped against a 200KB route budget, so the handful actually needed were written by
hand in `components/ui/controls.tsx` on native `<select>`, `<input type="range">` and
`<dialog>`.

That was reversed on 2026-09-05, on the same reasoning as the fonts: 4G is the realistic
floor now, not 2G. What is installed is **nine Radix primitives, not forty-eight** — the
ones something on screen actually uses — and `components/ui/` is now stock shadcn:

| | |
|---|---|
| `button` `input` `textarea` `label` `badge` | form and text primitives |
| `dropdown-menu` | the language switcher |
| `select` | styled listbox, where the design calls for a trigger |
| `slider` `progress` | the repayment planner and the fit bars |
| `dialog` | replaces the hand-rolled `<dialog>` wrapper in `Panel.tsx` |

`components.json` is checked in, so `npx shadcn@latest add <name>` works and lands
components that compile against this palette without being rewritten.

**What it cost.** The landing route went from 122KB to 162KB gzipped, and the worst route
in the app is 162KB of the 200KB budget. `scripts/check-bundle.mjs` still fails the build
if that stops being true.

**What did not change.** Three things survive the move, because they are accessibility
decisions rather than styling ones, and shadcn's defaults are worse on this device:

- **48px, not 40px.** Every control is `min-h-touch`. shadcn ships `h-10`; that is not a
  thumb target on a Rs 6,000 phone held one-handed outdoors. Menu and listbox rows are
  48px too, against shadcn's 32px.
- **`text-lg`, not `text-sm`.** The whole type scale in `tailwind.config.ts` is a step up
  from a typical web app, because this is read at arm's length in sunlight.
- **The native `<select>` stays.** `controls.tsx` still exports `SelectInput` on a real
  `<select>`, and the long option lists in the onboarding wizard still use it: on Android
  it opens the platform's own wheel, which is one tap, works under switch control, and
  needs no JavaScript. The shadcn Select is there for where the design wants a styled
  trigger. This is the one place shadcn is a step *down* on the target device, and both
  are kept rather than pretending otherwise.

The token values shadcn reads (`--primary`, `--muted-foreground`, `--destructive`, …) are
this project's audited palette rather than shadcn's slate defaults, so
`scripts/check-contrast.mjs` remains the authority. Two of shadcn's defaults would have
failed it outright: `--destructive` at #DC2626 is 4.02:1, and `--muted-foreground` at
#667085 is 4.29:1 and is the caption colour used on every screen.

## Not adopted, and why

**Recharts.** ~95KB for one stacked bar chart, which is ~200 lines of SVG instead. The
drop's other three charts were dropped rather than ported: a donut showing a single "92%
match" is a number wearing a costume, and the ministry pies were over categories with no
part-to-whole meaning.

**Google Fonts, as an `@import`.** The drop pulled Plus Jakarta Sans, Inter and JetBrains
Mono from `fonts.googleapis.com`, which blocks the first paint on a third-party stylesheet.
The first pass named the faces in the Tailwind config and loaded nothing. That was reversed
on 2026-09-05 — 2G is no longer the realistic floor, 4G is — and the same three faces now
load through `next/font/google` (`src/styles/fonts.ts`): fetched at build time and served
from this origin, as variable fonts, one file per family rather than four static cuts, with
`display: swap` and size-adjusted fallback metrics so the swap does not shift the layout.
116KB preloaded. Each `--font-*` variable sits at the *front* of its stack with Noto Sans
directly behind it, because none of the three carries Devanagari, Bengali, Tamil or Telugu.

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

## The top bar, in full

The first pass of the signed-in shell left two of the drop's controls out, with a reason
that was right about the fakes and wrong about the conclusion: a search box that searches
nothing and a bell that never rings are worse on a ministry-branded page than the space
they would fill. Both are now there, with real data behind them.

| The drop drew | Here |
|---|---|
| "Search schemes, partners…" | A WAI-ARIA combobox over the published catalogue (filtered in the browser, fetched once on first focus) and `GET /partners/directory?q=` (debounced, with out-of-order replies discarded). Not a shadcn Popover or Command: both move focus into the panel, and a combobox's caret has to stay in the input |
| A bell with an unread dot | `GET /citizen/notifications` — an endpoint added for it, over the `notifications` table that already existed. Every row is a message that was really sent, kept as it was sent. Nothing is composed on read, so an empty bell says "nothing yet". The dot is a `localStorage` watermark, not a read receipt |
| "My Shortlist" in the sidebar | `lib/shortlist.ts`, which stores scheme codes on the device and nothing else. A bookmark does not belong in a government record and nobody should have to consent to one — and it is the only shape that also works for the anonymous journey |
| "Judge Mode · 3-min tour" | The existing `/demo` console, which is that tour |
| "NBCFDC Term Loan · for OBC entrepreneurs · ₹15,00,000 · 100% match" on the dashboard | The layout verbatim; the figures from the engine. This repository's pack is three NSFDC schemes, Scheduled Caste only. Inventing a fourth scheme to match a mockup is the same mistake as the drop's invented counters |

Two smaller corrections came out of the same pass. The application-status tile printed
`status.replace(/_/g, " ")`, which renders `PARTNER_ACKNOWLEDGED` as "partner
acknowledged" and reads as a leaked internal — it now uses the `track.status` catalogue,
the same sentences the public tracking page shows, in all six languages. And
`GET /citizen/me` returned `users.display_name` rather than `citizens.display_name`, so
editing your name on the profile page changed nothing in the header.

## Density: the whole app at 80%

The drop was drawn at a density the 100% build did not reproduce — at 1080p the ported
layout reads as oversized, and the difference is almost exactly a browser zoom of 80%.
That is now the default: one `font-size: 80%` on `html`, which every `rem` in the system
follows.

What that number is *not* allowed to touch:

- **The 48px touch target.** A coarse pointer or a viewport under 1024px gets 100% back.
  `spacing.touch` is 3rem because 48px is the Android and iOS minimum for a one-handed
  outdoor tap, and this is the one product where that is not negotiable.
- **The reader's own font size.** A percentage, so someone who set a 20px base still gets
  16px. A hard `12.8px` would override them.
- **The measure.** The five page-container widths are named in `tailwind.config.ts` and
  pre-divided by the 0.8, so the content column stays where it was drawn instead of
  stranding a fifth of a wide monitor.

Hover feedback was rebuilt in the same pass. The drop transitioned `box-shadow`, which
repaints the whole element every frame; `.lift` paints the shadow once into a
pseudo-element and animates its opacity, with the lift itself a transform. Both are
compositor properties. `apps/web/scripts/measure-frames.mjs` measures it and fails on a
`box-shadow` transition reappearing.

## The landing page, in full

The first pass ported the design system and the eight signed-in screens but left the
front page as a short version of the drop's. It is now the whole thing — header with
navigation, hero with the match-flow card, live counters, the four-step journey, the
story carousel, the scheme cards, the closing panel and the footer.

The layout is the drop's. Every number on it is either fetched or derived, and this is
where each one comes from:

| Section | Fed by |
|---|---|
| Match-flow card in the hero | `lib/schemeFacts.ts` + `lib/emi.ts`, rendered on the server. The instalment is `repaymentPlan()` — the same function the calculator screen uses — over the seeded persona's Rs 10,80,000 at the rule pack's 8% for 84 months with a 6-month moratorium |
| Counters | `/schemes` and `/partners/coverage`, at runtime |
| Story carousel | The three personas `scripts/seed/demo.py` creates. District, category, trade, scheme and amount are the ones in the database after `make demo` |
| Scheme cards | `lib/schemeFacts.ts`, mirrored from `packages/rules/dist/rules.json` and pinned to it by `schemeFacts.test.ts` |
| Closing panel | The same worked example as the hero, so the page never shows two different best matches |

Three claims in the drop's copy were changed rather than reproduced, because the product
does not do what they say:

| The drop said | Here | Why |
|---|---|---|
| "AI Matching · 6 schemes evaluated" | "Rules checked · 3 schemes evaluated" | CLAUDE.md rule 1. No model decides eligibility, and the front page is the worst place to imply one does. Three is the number of schemes in the pack |
| "Ranked recommendations with explainable AI scoring" | "…each with the rule that put it there" | The fit score is deterministic — `packages/rules/src/setu_rules/fit.py` — not a model output |
| "Realtime" on the hero card | "Rule pack · 2026-08-29" | The card is a worked example computed at build time. A badge that says live when it is not is the one thing this page cannot do |

**"Entrepreneurs guided"** has no honest source — there is no public endpoint that counts
citizens, and there should not be one. That tile shows districts with a Channel Partner,
which is real and is the thing a citizen actually wants to know.

**The carousel rotates**, seven seconds a slide, which is the drop's behaviour. An
auto-rotating carousel moves the sentence someone is halfway through reading, so the
rotation carries the four things that make it safe: a pause button (WCAG 2.2.2 asks for a
mechanism, and hover is not one — it does not exist on a touchscreen and is unreachable
from a keyboard), pause on hover and on focus, a full stop under
`prefers-reduced-motion`, and a timer that restarts on every change so a manual tap never
lands two seconds before the next move. `aria-live` is `off` while it rotates and
`polite` once a person is driving it, because a live region that changes every seven
seconds interrupts a screen reader continuously.

**Photographs** are hotlinked from Wikimedia Commons under CC BY-SA 4.0 and credited
under the carousel; `next.config.js` allows that one host and nothing else, and Next
resizes and re-encodes each file on the way through, because the originals are 200-450KB
of JPEG and the citizen route is budgeted for 2G. They are stock images of the trades,
not photographs of the people named, and the section says so in every language.

## The name

The product is **SamarthSetu**, the name the design drop carried, in place of the earlier
SETU. The name is transliterated in each catalogue rather than left in Latin script —
समर्थ सेतु, সমর্থ সেতু, சமர்த் சேது — following the convention the catalogues already
used. Two things deliberately kept the old token because they are identifier formats and
not the product name: the `SETU` marker inside synthetic IFSC codes (`SBIN0SETU07`) and
the application reference prefix (`SETU-2026-MH-000431`).
