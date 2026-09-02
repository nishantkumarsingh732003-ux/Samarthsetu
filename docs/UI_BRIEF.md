# SETU — UI brief

A self-contained prompt for an AI UI builder (v0, Lovable, Bolt, Figma Make) or a
designer. Paste the whole thing. Everything below describes a system that already works;
what comes back has to drop into it, so the constraints and the tokens are not
suggestions.

---

## The product

**SETU** — a government scheme discovery, eligibility and routing service for India's
Ministry of Social Justice & Empowerment (Smart India Hackathon 2026, PS 26092).

A Scheduled Caste entrepreneur or student cannot answer two questions:

1. Which government credit scheme actually fits me?
2. Which of the 100+ Channel Partners near me is authorised to process *that* scheme?

So they guess, walk into the wrong bank branch, and get turned away. Nobody queues twice.

SETU answers both, explains every answer, and routes them to a branch that can actually
help. **It does not approve loans** — it matches and routes; a Channel Partner decides.
Every screen must say so.

## Who is on the other side of the screen

Design for **her**, not for a reviewer:

- A woman selling vegetables in Nagpur, on a **₹6,000 Android over 2G**
- Reads Hindi more comfortably than English; may not read fluently at all
- Outdoors, in sunlight, one-handed, possibly with a cracked screen
- Has been turned away from a branch before and will not go twice

This means: large type, high contrast, few choices per screen, plain words, and never a
dead end. If a screen says "no", it must say **why** and **what to do instead**.

---

## Hard constraints — the build fails without these

These are enforced by automated gates. Generated UI that ignores them cannot be merged.

| Constraint | Limit | Why |
|---|---|---|
| **JS budget** | **< 200 KB gzipped** per citizen route (currently 114 KB) | 2G. This is the product, not a nice-to-have |
| **Contrast** | WCAG AA on every foreground/background pair | Sunlight, low vision |
| **Touch targets** | ≥ 48 px | One-handed, outdoors |
| **Languages** | 6 — English, हिन्दी, मराठी, বাংলা, தமிழ், తెలుగు | No hardcoded strings anywhere |
| **Offline** | Core screens must render with no network | Dead spots are normal |

**Therefore, do not use:** component libraries that ship large runtimes (Radix, MUI,
Chakra, Mantine), animation libraries (framer-motion), icon packs imported wholesale,
Google Fonts beyond the one already chosen, or carousels/parallax/gradients.

**Do use:** plain React + Tailwind, semantic HTML, inline SVG for the handful of icons
needed, CSS transitions if anything must move.

---

## The design system that already exists

Match it exactly. This is a real Tailwind config in the repo.

### Colour

```
canvas       #F7F5F1   warm paper ground, not clinical white
surface      #FFFFFF   cards
ink          #1A1D21   body text        (14.8:1 on canvas)
ink-muted    #4A5159   secondary text
ink-faint    #5E6672   captions         (5.33:1 — the floor)
line         #DFDBD4   hairlines, borders

accent-50    #EDF3F8   chips, callout grounds
accent-100   #D6E4EF
accent-600   #12557F   meters, bars
accent-700   #0E4266   primary buttons, links  (7.4:1 on white)
accent-800   #0A3350   pressed

good  bg #E8F3EC  fg #1B5E33  line #B7DCC4    eligible
warn  bg #FDF3E3  fg #7A4E0A  line #EFD9AE    caution, unreviewed
stop  bg #FBECEA  fg #8A2318  line #EEC8C2    blocked, error
```

**One accent, a warm neutral ground, a restrained semantic set.** Deliberately no
gradients and no purple — this is a public service, not a SaaS landing page. Semantic
colour (good/warn/stop) is separate from the accent and never used decoratively.

### Type

One family, `Noto Sans`, because it carries Devanagari, Bengali, Tamil **and** Telugu —
so all six languages share a typeface instead of falling back to whatever the phone has.

```
base  1.0625rem / 1.6     deliberately larger than a typical web app
lg    1.1875rem / 1.55
xl    1.375rem  / 1.4
2xl   1.75rem   / 1.3
3xl   2.125rem  / 1.2
```

### Shape and spacing

```
rounded-card   0.75rem
shadow-card    0 1px 2px rgba(26,29,33,.05), 0 1px 8px rgba(26,29,33,.04)
min-h-touch    3rem (48px) — every interactive control
```

### Existing classes — reuse, do not reinvent

```css
.btn-primary    accent-700 bg, white text, 48px min height, rounded-card
.btn-secondary  white bg, 2px line border, ink text, hovers to accent-600
.card           white, 1px line border, rounded-card, shadow-card
.skip-link      visually hidden until focused
```

---

## Screens

### Citizen surface — 7 screens, all six languages, inside the JS budget

---

**1. `/` — language picker**

The only screen before a language exists. Six large tap targets, each label in its **own
script** (हिन्दी, not "Hindi"). No flags. Nothing else on the page but the service name
and one line of what it does.

---

**2. `/[locale]` — home**

One primary action, named for what it does — *"Find my scheme"*, not *"Start"*. One line
of reassurance underneath. A small link to track an existing application by reference
number. That is the whole screen.

---

**3. `/[locale]/assist` — the conversation**

Voice-first. A large microphone button (with a typed fallback that is equally
prominent, never hidden behind "advanced").

- Progress: *"Question 3 of at most 6"*
- Answers already given appear as **tappable chips** so a mis-heard income can be
  corrected — a wrong income is the difference between eligible and not
- Multiple-choice questions render as large buttons, not a dropdown
- A "read aloud" control on every question

Real exchange:

> **SETU:** आपको कुल कितने पैसे की ज़रूरत है?
> **Citizen:** 80 hazaar
> **SETU:** आप किस सामाजिक श्रेणी से हैं?  [SC] [ST] [OBC] [GENERAL]

---

**4. `/[locale]/results` — the answer**

The most important screen in the product. A ranked list of scheme cards. **Ineligible
schemes are shown, greyed, never hidden** — a citizen told nothing assumes we never
considered them.

Each card carries, in this order:

- The **official scheme name, verbatim, in Latin script** — legal names are never
  translated (a transliterated gloss may sit beneath)
- Verdict badge: *You may be eligible* / *…with a note* / *We need more information* /
  *Not available to you*
- Indicative amount and interest — always labelled **indicative**
- **"Why this ranking?"** — expands to five bars, each with a score out of 100 and a
  plain sentence
- **"Why this scheme?"** / **"Why not this scheme?"** — expands to reasons, each with a
  rule ID in monospace
- For a blocked card: **"Consider instead: Term Loan"**
- A primary action: *"Find an office near me"*

Real card content:

```
Micro Finance Scheme                          You may be eligible
Up to about Rs 72,000 · Interest 6.5% · Covers up to 90% of cost

Why this ranking?                                        99.5 / 100
  Funds what you need      100  ▓▓▓▓▓▓▓▓▓▓  This scheme funds an enterprise project.
  Amount fits the scheme   100  ▓▓▓▓▓▓▓▓▓▓  Rs 80,000 sits well inside the Rs 140,000 ceiling.
  You meet the rules       100  ▓▓▓▓▓▓▓▓▓▓  You meet every requirement.
  Cost of the loan          97  ▓▓▓▓▓▓▓▓▓░  6.5% interest and covers up to 90% of the cost.
  How much we know         100  ▓▓▓▓▓▓▓▓▓▓  We have everything this scheme asks.

Why this scheme?
  MF_CATEGORY_SC     You are a Scheduled Caste applicant.
  MF_INCOME_CEILING  Your annual family income is within the Rs 5,00,000 ceiling.
```

A greyed card:

```
Term Loan                                        Not available to you   [dimmed]
Why not this scheme?
  TL_PROJECT_COST_FLOOR  The Term Loan is for units costing more than Rs 1,40,000.
Consider instead: Micro Finance Scheme
```

Footer, always: *"Amounts are indicative. A Channel Partner decides your loan."*

---

**5. `/[locale]/results/[scheme]/partners` — where to go**

Ranked branches. A map toggle (map is lazy-loaded and off by default — most citizens
never open it).

Each branch: rank, name, type (*State agency / Public sector bank / Regional rural bank /
Microfinance institution*), distance, typical turnaround, how busy. **"Why this order?"**
expands to four labelled meters — Distance, Speed, Suited to this scheme, Capacity — so
she can see a closer branch lost because it was busy.

**Then the screen that matters most in the entire product:**

```
⚠ Nearby, but cannot help
These offices are close to you but cannot process this scheme.

  Bank of Maharashtra, Nagpur
  is 4.2 km away but is not authorised for the Micro Finance Scheme.
  [NOT_AUTHORISED]

  Fusion Micro Finance, Nagpur
  is 9.5 km away but has paused new applications because its capacity is exhausted.
  [NOT_ACCEPTING]
```

Give this section real visual weight — a warn-toned bordered panel. It is the single
clearest proof the product solves the stated problem.

Footer: *"Office details are demo data pending the official partner list."*

---

**6. `/[locale]/apply/[scheme]` — submit**

Says up front: *"SETU does not give loans. This sends your application to the office you
chose, and that office decides."*

Every field **optional except consent**: name, phone, Aadhaar number. Under each, what
happens to it — *"We keep only the last 4 digits. The full number is never stored."*

Then the **document checklist**, each with a reason (*"This proves you are from a
Scheduled Caste, which every NSFDC scheme requires"*).

Consent is an **unticked checkbox with the consequence written beside it**. A pre-ticked
box is not consent. Submit is disabled until it is ticked.

---

**7. `/[locale]/track/[ref]` — after**

No login. The reference number is the key.

- The reference in **large, selectable, monospace** type — it gets read aloud down a
  phone line at a counter: `SETU-2026-MH-000001`
- A vertical status timeline, completed steps filled in accent, current step bold:
  Submitted → Office has your application → Documents requested → Under review →
  Approved → Money released
- Documents: each with why it is needed, a **"Take a photo"** button (opens the camera),
  and any warning — *"This appears to be dated 2019. Most offices require one issued
  within the last 6 months."*
- Confirmation where relevant: *"The ID number in this photo has been blacked out."*

---

### Staff surface — 3 screens, English only, no JS budget

Desk tools. You can be more generous here. Still institutional, still calm.

---

**8. `/console/login`** — one form, both roles. Email, password. The role in the response
decides where you land.

---

**9. `/console/partner` — branch officer's queue**

Answers *"what do I pick up next?"* without opening anything.

- **Intake capacity** panel at the top: a toggle per scheme, Accepting / Paused. Toggling
  removes this branch from citizen routing immediately
- Each queue row: reference number, scheme, applicant name and district, amount,
  **days open against this branch's own stated turnaround** as a coloured pill
  (green on track / amber due / red breached)
- A **document readiness meter** with the missing items named
- Masked identity line: `AADHAAR ···· 0123 · phone ···· 3210 · verify in person`
- **"Why was this routed here?"** expands to the rule IDs
- Actions: Accept, Request documents, Start appraisal, Sanction, Mark disbursed, Reject.
  Reject and Request-documents require a typed reason

---

**10. `/console/admin` — ministry dashboard**

A government decision-support tool, not an analytics template. No vanity charts.

- **Misrouting prevented** — the headline, in a bordered panel: one very large number
  (2,338) with a four-way breakdown: not authorised or paused / beyond reach / wrong
  ticket size / sent to a better-fitting scheme
- **Funnel**, 7 stages, horizontal bars, with the **largest loss called out in words**:
  *"Largest loss: Picked up → Sanctioned — 80% of people did not continue"*
- **Underserved districts** — a table, and this is where a **map is still missing** (the
  one real UI gap; see below):

  ```
  District          Demand  Partners  Families unserved
  Lucknow, UP            4         7  education loan
  Nagpur, MH             4         6  education loan
  Kolkata, WB            3         2  education loan
  ```

  *Seven partners in Lucknow and not one can process an Educational Loan.* Frame this as
  a procurement instrument.
- Smaller panels: scheme mix, language of service, application status, turnaround by
  partner type (median and p90). Bars are `div`s — a screen reader gets the number
- CSV export on every section

**The one genuine gap:** underserved districts should also render as a **map of India**
with district bubbles sized by demand and coloured by coverage. Leaflet is already in the
project. This is the highest-value screen to design.

---

## Rules for the copy

Words are design material here.

- **Never** say the system approved, sanctioned or granted anything. It *matches* and
  *routes*
- Official scheme names verbatim, never translated: *Micro Finance Scheme*, *Term Loan*,
  *Educational Loan Scheme*
- Amounts always labelled *indicative*
- Indian digit grouping — **₹1,40,000**, never ₹140,000
- A refusal always carries a reason and a next step
- Plain words: *"office"* not *"channel partner"*, *"what you need to bring"* not
  *"documentation requirements"*
- Unreviewed translations are **badged**, not hidden: *"This text has not yet been
  checked by a Tamil speaker."*

---

## What to deliver

React + Tailwind, one file per screen, using the exact tokens above. Real content from
this brief — **no lorem ipsum, no placeholder names**. Mobile-first: design at 360 px
wide, then let it breathe on desktop.

If you only do one thing, do **`/[locale]/results`** — the scheme cards with the ranking
breakdown, the greyed ineligible cards, and the "why not" reasons. That screen is the
product.

If you do a second, do the **admin map**.

---

## What not to do

- No dashboards for the citizen. She wants one answer, not a control panel
- No dark mode for the citizen surface — outdoor daylight legibility is the case that matters
- No hero images, no illustrations of smiling people holding money
- No progress rings, no confetti, no skeleton shimmer
- No hiding the ineligible schemes to make the screen look tidier
- No "AI" branding anywhere. The intelligence is that the rules are auditable, and
  claiming otherwise is the thing this project exists to avoid
