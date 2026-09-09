/**
 * Rule id -> the short criterion label the card shows.
 *
 * The design lists passed criteria as scannable labels — "Family income supported" —
 * rather than as the engine sentence, which runs to a line and a half and turns a
 * four-item grid into a wall. The engine sentence is not thrown away: it rides along in
 * the `title` of the same row, and the blocked ones are printed in full when the citizen
 * opens "Why not this scheme?". Nothing that was traceable stops being traceable.
 *
 * The mapping is on the id, not on the message text, because ids are stable across
 * rewordings and across all six languages. Every rule in `packages/rules/schemes` is
 * covered by `criteriaLabels.test.ts`; a new rule with no entry here falls back to the
 * engine sentence rather than to a blank, so the failure mode is verbose, not silent.
 */

/** The suffix a rule id ends with, longest first so `PROJECT_COST_CEILING` is tested
 *  before `CEILING` would be. Value is the message key under `matches.criteria`. */
const BY_SUFFIX: readonly (readonly [string, string])[] = [
  ["CATEGORY_SC", "socialCategory"],
  ["INCOME_CEILING", "familyIncome"],
  ["PROJECT_COST_FLOOR", "projectCost"],
  ["PROJECT_COST_CEILING", "projectCost"],
  ["PROJECT_COST_BAND", "projectCost"],
  ["NOT_FOR_EDUCATION", "enterpriseType"],
  ["PURPOSE_IS_EDUCATION", "coursePurpose"],
  ["ADMISSION_CONFIRMED", "admission"],
  ["LOAN_CAP_BINDS", "fundingShare"],
];

/** The `matches.criteria.*` key for a rule, or null when the rule is not one this
 *  mapping knows — in which case the caller shows the engine sentence instead. */
export function criterionKey(ruleId: string): string | null {
  for (const [suffix, key] of BY_SUFFIX) {
    if (ruleId.endsWith(suffix)) return key;
  }
  return null;
}
