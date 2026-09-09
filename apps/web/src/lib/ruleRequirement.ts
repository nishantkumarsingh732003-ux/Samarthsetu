/**
 * Turn a rule's published expression into the requirement it implies.
 *
 * The eligibility rows show "Your: SC · Req: SC" — and the right-hand half has to come
 * from somewhere. It is not in `limits`: an income ceiling of Rs 5,00,000 lives only
 * inside `MF_INCOME_CEILING`'s condition, not in any structured field. So it is read off
 * the condition, which the API already publishes verbatim as `when_source` and which the
 * Eligibility tab already prints in full underneath.
 *
 * The one thing to keep straight: `when_source` is the *blocking* condition. A rule fires
 * when it is true, so the requirement is its negation — `annual_family_income > 500000`
 * blocks, therefore the requirement is "up to 5,00,000". Getting that backwards would
 * print a ceiling as a floor, so `negate` below is exhaustive over the six operators and
 * `ruleRequirement.test.ts` asserts every rule in the published pack round-trips.
 *
 * Deliberately not a general expression parser. Every rule in the pack is a single
 * `profile.<field> <op> <literal>` comparison; anything else returns null and the caller
 * falls back to printing the rule's own sentence. A parser that guessed at `and`/`or`
 * would eventually render a requirement that is not the rule, which is worse than
 * rendering no requirement at all.
 */

/** The comparison as the *requirement* reads, after negating the blocking condition. */
export type RequirementOp = "eq" | "ne" | "lte" | "lt" | "gte" | "gt";

export interface Requirement {
  /** Profile field the rule reads, e.g. `annual_family_income`. */
  field: string;
  op: RequirementOp;
  value: string | number | boolean;
}

const PATTERN = /^profile\.([a-z_][a-z0-9_]*)\s*(==|!=|>=|<=|>|<)\s*(.+?)\s*$/;

/** Blocking operator -> the operator the requirement is stated with. */
const NEGATE: Record<string, RequirementOp> = {
  "==": "ne",
  "!=": "eq",
  ">": "lte",
  ">=": "lt",
  "<": "gte",
  "<=": "gt",
};

function literal(raw: string): string | number | boolean | undefined {
  if (raw === "true") return true;
  if (raw === "false") return false;
  const quoted = /^'([^']*)'$/.exec(raw) ?? /^"([^"]*)"$/.exec(raw);
  if (quoted) return quoted[1];
  if (/^-?\d+(\.\d+)?$/.test(raw)) return Number(raw);
  return undefined;
}

/** The requirement a rule states, or null if its condition is not a single comparison. */
export function requirementFrom(whenSource: string): Requirement | null {
  const match = PATTERN.exec(whenSource.trim());
  if (!match) return null;

  const [, field, operator, raw] = match;
  const value = literal(raw);
  if (value === undefined) return null;

  return { field, op: NEGATE[operator], value };
}

/** Fields whose values are rupee amounts, so the caller knows to format them as money
 *  rather than as a bare count. Derived from the field name, which the rule pack keeps
 *  consistent — `*_income` and `*_cost` are the only monetary profile fields. */
export function isMoneyField(field: string): boolean {
  return field.endsWith("_income") || field.endsWith("_cost");
}
