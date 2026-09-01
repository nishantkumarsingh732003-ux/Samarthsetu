/**
 * Why a scheme ranked where it did — the TypeScript half of `setu_rules/fit.py`.
 *
 * This is a deliberate line-by-line port rather than a reimplementation. The
 * conformance suite compares this engine's full output against Python's, so any
 * divergence here — a different rounding, a different threshold, a reworded sentence —
 * fails CI. That is the point: the citizen app may one day evaluate offline on the
 * device, and it must reach the same conclusion *and give the same reasons* as the
 * server did.
 *
 * As in Python, `evaluate` ranks on this score, with `rankKey` and the scheme code
 * underneath it so a tie can never fall through to iteration order. Partner availability
 * is deliberately not a component: a stored decision whose score moved when a branch
 * paused intake would stop being replayable.
 */
import type { FitComponent, FitScore, MatchResult, Profile, Scheme } from "./types";

/** Shares of the total. They sum to 1.0, asserted by a test rather than by hope. */
export const FIT_WEIGHTS: Record<string, number> = {
  purpose_fit: 0.3,
  amount_fit: 0.25,
  category_fit: 0.2,
  cost_of_credit: 0.15,
  information: 0.1,
};

const EDUCATION = "EDUCATION_LOAN";

// NSFDC concessional credit sits in a 6.5-8% band, so 6.5% scores 100 and 8% scores 0.
const CHEAPEST_RATE = 6.5;
const DEAREST_RATE = 8.0;

// A project using more than this share of the ceiling has little room if costs rise.
const COMFORTABLE_SHARE = 0.8;

/** Python rounds half-to-even; JS Math.round rounds half-up. One decimal place keeps
 *  the two in step for every value the components can actually produce. */
function round1(value: number): number {
  return Math.round(value * 10) / 10;
}

function round2(value: number): number {
  return Math.round(value * 100) / 100;
}

function clamp(value: number): number {
  return round1(Math.max(0, Math.min(100, value)));
}

/** Matches Python's `f"{value:,.0f}"` — the thousands separator the citizen sees. */
function money(value: number): string {
  return Math.round(value).toLocaleString("en-US");
}

function component(key: string, score: number, detail: string): FitComponent {
  const weight = FIT_WEIGHTS[key];
  return { key, score, weight, contribution: round2(score * weight), detail };
}

function purposeFit(scheme: Scheme, profile: Profile): FitComponent {
  const sector = profile.project_sector;
  const isEducationScheme = String(scheme.family) === EDUCATION;

  if (sector === null || sector === undefined) {
    return component("purpose_fit", 50, "We do not know yet what the money is for.");
  }

  const wantsEducation = sector === "EDUCATION";
  if (wantsEducation === isEducationScheme) {
    return component(
      "purpose_fit",
      100,
      wantsEducation
        ? "This scheme funds a course."
        : "This scheme funds an enterprise project.",
    );
  }
  return component(
    "purpose_fit",
    0,
    isEducationScheme
      ? "This scheme funds a course, and you asked about a business."
      : "This scheme funds a business, and you asked about studies.",
  );
}

function amountFit(scheme: Scheme, profile: Profile): FitComponent {
  const raw = profile.project_cost;
  const floor = scheme.limits.min_project_cost;
  const ceiling = scheme.limits.max_project_cost;

  if (raw === null || raw === undefined) {
    return component("amount_fit", 50, "We do not know the amount yet.");
  }

  const cost = raw as number;
  if (ceiling !== null && cost > ceiling) {
    return component(
      "amount_fit",
      0,
      `Rs ${money(cost)} is above this scheme's Rs ${money(ceiling)} ceiling.`,
    );
  }
  if (floor !== null && cost < floor) {
    return component(
      "amount_fit",
      0,
      `Rs ${money(cost)} is below this scheme's Rs ${money(floor)} floor.`,
    );
  }
  if (ceiling === null) {
    return component(
      "amount_fit",
      90,
      "This scheme sets no ceiling on the cost of the course.",
    );
  }

  const used = cost / ceiling;
  const score =
    used <= COMFORTABLE_SHARE
      ? 100
      : 100 - ((used - COMFORTABLE_SHARE) / (1 - COMFORTABLE_SHARE)) * 40;
  const detail =
    used <= COMFORTABLE_SHARE
      ? `Rs ${money(cost)} sits well inside the Rs ${money(ceiling)} ceiling.`
      : `Rs ${money(cost)} is close to the Rs ${money(ceiling)} ceiling, so there is ` +
        "little room if costs rise.";
  return component("amount_fit", clamp(score), detail);
}

function categoryFit(result: MatchResult): FitComponent {
  if (result.verdict === "ELIGIBLE") {
    return component("category_fit", 100, "You meet every requirement.");
  }
  if (result.verdict === "LIKELY_ELIGIBLE") {
    return component("category_fit", 80, "You meet every requirement, with a note to check.");
  }
  if (result.verdict === "NEED_MORE_INFO") {
    const missing = result.missing_fields.length;
    return component(
      "category_fit",
      50,
      missing === 1
        ? "One more answer is needed to be sure."
        : `${missing} more answers needed to be sure.`,
    );
  }
  const blocker = result.blocked_because[0]?.message ?? "A rule blocks this.";
  return component("category_fit", 0, blocker);
}

/** Matches Python's `f"{value:g}"` for the rates and percentages in the rule data. */
function trimNumber(value: number): string {
  return String(value);
}

function costOfCredit(scheme: Scheme): FitComponent {
  const rate = scheme.limits.interest_rate_min;
  const pct = scheme.limits.max_funding_pct;

  const rateScore =
    rate === null ? 50 : clamp(100 - ((rate - CHEAPEST_RATE) / (DEAREST_RATE - CHEAPEST_RATE)) * 100);
  const fundingScore = pct === null ? 50 : clamp(pct);
  const score = clamp(rateScore * (2 / 3) + fundingScore * (1 / 3));

  const parts: string[] = [];
  if (rate !== null) parts.push(`${trimNumber(rate)}% interest`);
  if (pct !== null) parts.push(`covers up to ${trimNumber(pct)}% of the cost`);

  // Python's str.capitalize() upper-cases the first character and lower-cases the rest.
  const joined = parts.length ? `${parts.join(" and ")}.` : "";
  const detail = joined
    ? joined.charAt(0).toUpperCase() + joined.slice(1).toLowerCase()
    : "Terms are not published.";
  return component("cost_of_credit", score, detail);
}

function information(result: MatchResult): FitComponent {
  const missing = result.missing_fields.length;
  if (missing === 0) {
    return component("information", 100, "We have everything this scheme asks.");
  }
  return component(
    "information",
    clamp(100 - missing * 25),
    missing === 1 ? "One answer still missing." : `${missing} answers still missing.`,
  );
}

/** The full breakdown for one scheme. Pure, deterministic, no I/O. */
export function fitScore(scheme: Scheme, result: MatchResult, profile: Profile): FitScore {
  const components = [
    purposeFit(scheme, profile),
    amountFit(scheme, profile),
    categoryFit(result),
    costOfCredit(scheme),
    information(result),
  ];
  return {
    total: round1(components.reduce((sum, c) => sum + c.contribution, 0)),
    components,
  };
}
