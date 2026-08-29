import bundleJson from "../../dist/rules.json";
import { evaluateNode, UNKNOWN } from "./evaluate";
import { FIELDS } from "./fields";
import type {
  MatchResult,
  MatchRun,
  NextQuestion,
  Profile,
  Reason,
  RuleBundle,
  Scheme,
  Verdict,
} from "./types";

export const bundle = bundleJson as unknown as RuleBundle;
export const ENGINE_VERSION = bundle.engine_version;
export const RULES_DIGEST = bundle.rules_digest;

/**
 * Whether a speaker of `language` has reviewed the copy. Compiled into the bundle by
 * the Python side so the browser and the API cannot disagree about it.
 */
export function translationStatus(language: string): string {
  return bundle.translation_status?.[language] ?? "fallback";
}

const NO_CEILING = Number.POSITIVE_INFINITY;

const VERDICT_ORDER: Record<Verdict, number> = {
  ELIGIBLE: 0,
  LIKELY_ELIGIBLE: 1,
  NEED_MORE_INFO: 2,
  INELIGIBLE: 3,
};

function message(mapping: Record<string, string>, language: string): string {
  return mapping[language] || mapping.en || "";
}

/** Match Python's `round(value, places)` for the magnitudes this engine produces. */
function roundTo(value: number, places: number): number {
  const factor = 10 ** places;
  return Math.round(value * factor) / factor;
}

export function indicativeAmount(scheme: Scheme, profile: Profile): number | null {
  const cost = profile.project_cost;
  if (cost === null || cost === undefined) return null;

  const pct = scheme.limits.max_funding_pct;
  const funded = pct !== null ? (cost as number) * (pct / 100) : (cost as number);
  // The loan cap, not the project-cost band. See the Python docstring.
  const cap = scheme.limits.max_loan_amount;
  return roundTo(cap === null ? funded : Math.min(funded, cap), 2);
}

export function evaluateScheme(
  scheme: Scheme,
  profile: Profile,
  language = "en",
): MatchResult {
  const blocked: Reason[] = [];
  const matched: Reason[] = [];
  const warnings: Reason[] = [];
  const missing = new Set<string>();
  let redirect: string | null = null;

  const hardRules = scheme.rules.filter((r) => r.severity === "HARD_BLOCK");
  let decidedHard = 0;

  for (const rule of scheme.rules) {
    const outcome = evaluateNode(rule.when, profile);

    if (outcome === UNKNOWN) {
      if (rule.severity === "HARD_BLOCK") {
        for (const field of rule.fields) {
          const value = profile[field];
          if (value === null || value === undefined) missing.add(field);
        }
      }
      continue;
    }

    if (rule.severity === "HARD_BLOCK") decidedHard += 1;

    if (outcome === true) {
      const reason: Reason = {
        rule_id: rule.id,
        message: message(rule.message_i18n, language),
        severity: rule.severity,
      };
      if (rule.severity === "HARD_BLOCK") blocked.push(reason);
      else warnings.push(reason);
      if (redirect === null && rule.suggest_instead) redirect = rule.suggest_instead;
    } else if (Object.keys(rule.satisfied_i18n).length > 0) {
      matched.push({
        rule_id: rule.id,
        message: message(rule.satisfied_i18n, language),
        severity: rule.severity,
      });
    }
  }

  let verdict: Verdict;
  let confidence: number;
  if (blocked.length > 0) {
    verdict = "INELIGIBLE";
    confidence = 1.0;
  } else if (missing.size > 0) {
    verdict = "NEED_MORE_INFO";
    confidence = hardRules.length ? roundTo(decidedHard / hardRules.length, 4) : 0.0;
  } else if (warnings.length > 0) {
    verdict = "LIKELY_ELIGIBLE";
    confidence = 1.0;
  } else {
    verdict = "ELIGIBLE";
    confidence = 1.0;
  }

  const band =
    scheme.limits.interest_rate_min !== null && scheme.limits.interest_rate_max !== null
      ? ([scheme.limits.interest_rate_min, scheme.limits.interest_rate_max] as [number, number])
      : null;

  return {
    scheme_code: scheme.code,
    official_name: scheme.official_name,
    family: scheme.family,
    verdict,
    confidence,
    matched_because: matched,
    blocked_because: blocked,
    warnings,
    missing_fields: [...missing].sort(),
    indicative_amount: verdict === "INELIGIBLE" ? null : indicativeAmount(scheme, profile),
    indicative_interest_band: band,
    max_funding_pct: scheme.limits.max_funding_pct,
    redirect_suggestion: redirect,
    needs_verification: scheme.provenance.needs_verification,
    provenance: scheme.provenance,
    rank: null,
    translation_status: translationStatus(language),
  };
}

function rankKey(scheme: Scheme, profile: Profile): [number, number, number] {
  const cost = profile.project_cost;
  const ceiling = scheme.limits.max_project_cost;

  let headroom = NO_CEILING;
  if (cost !== null && cost !== undefined && ceiling !== null) {
    const slack = ceiling - (cost as number);
    headroom = slack < 0 ? NO_CEILING : slack;
  }

  const interest = scheme.limits.interest_rate_min ?? NO_CEILING;
  const funding = -(scheme.limits.max_funding_pct ?? 0);
  return [headroom, interest, funding];
}

export function evaluate(profile: Profile, language = "en"): MatchResult[] {
  const byCode = new Map(bundle.schemes.map((s) => [s.code, s]));
  const results = bundle.schemes.map((s) => evaluateScheme(s, profile, language));

  results.sort((a, b) => {
    const va = VERDICT_ORDER[a.verdict];
    const vb = VERDICT_ORDER[b.verdict];
    if (va !== vb) return va - vb;

    const ka = rankKey(byCode.get(a.scheme_code)!, profile);
    const kb = rankKey(byCode.get(b.scheme_code)!, profile);
    for (let i = 0; i < ka.length; i += 1) {
      if (ka[i] !== kb[i]) return ka[i] < kb[i] ? -1 : 1;
    }
    return a.scheme_code < b.scheme_code ? -1 : a.scheme_code > b.scheme_code ? 1 : 0;
  });

  return results.map((r, i) => ({ ...r, rank: i + 1 }));
}

export function fieldImpact(
  profile: Profile,
): Record<string, { rules: Set<string>; schemes: Set<string> }> {
  const impact: Record<string, { rules: Set<string>; schemes: Set<string> }> = {};

  for (const scheme of bundle.schemes) {
    const hardRules = scheme.rules.filter((r) => r.severity === "HARD_BLOCK");
    const outcomes = hardRules.map((rule) => [rule, evaluateNode(rule.when, profile)] as const);

    // A scheme with a definite block is settled; asking more about it changes nothing.
    if (outcomes.some(([, outcome]) => outcome === true)) continue;

    for (const [rule, outcome] of outcomes) {
      if (outcome !== UNKNOWN) continue;
      for (const field of rule.fields) {
        const value = profile[field];
        if (value !== null && value !== undefined) continue;
        impact[field] ??= { rules: new Set(), schemes: new Set() };
        impact[field].rules.add(rule.id);
        impact[field].schemes.add(scheme.code);
      }
    }
  }
  return impact;
}

/**
 * `exclude` names fields already put to the citizen. Asking the same question every
 * turn because they keep not answering it makes no progress and reads as broken.
 */
export function nextBestQuestion(
  profile: Profile,
  exclude?: Iterable<string>,
): NextQuestion | null {
  const impact = fieldImpact(profile);
  const skip = new Set(exclude ?? []);
  const remaining = Object.keys(impact).filter((f) => !skip.has(f));
  const names = remaining.length > 0 ? remaining : Object.keys(impact);
  if (names.length === 0) return null;

  names.sort((a, b) => {
    const byCount = impact[b].rules.size - impact[a].rules.size;
    if (byCount !== 0) return byCount;
    const byPriority = FIELDS[a].priority - FIELDS[b].priority;
    if (byPriority !== 0) return byPriority;
    return a < b ? -1 : 1;
  });

  const name = names[0];
  const field = FIELDS[name];
  return {
    field: name,
    question_i18n: { ...field.question_i18n },
    kind: field.kind,
    choices: field.choices ?? null,
    resolves_rules: [...impact[name].rules].sort(),
    resolves_schemes: [...impact[name].schemes].sort(),
  };
}

export function run(profile: Profile, language = "en"): MatchRun {
  const snapshot: Record<string, unknown> = {};
  for (const key of Object.keys(profile).sort()) snapshot[key] = profile[key];

  return {
    engine_version: ENGINE_VERSION,
    rules_digest: RULES_DIGEST,
    input_snapshot: snapshot,
    results: evaluate(profile, language),
    next_question: nextBestQuestion(profile),
  };
}
