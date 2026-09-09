"use client";

/**
 * One row per eligibility criterion: what the citizen answered, against what the rule
 * requires, and whether the engine passed it.
 *
 * Three surfaces render this — the eligibility sheet, the "why not" sheet, and the
 * Eligibility tab on the scheme page — and they must agree to the digit. A citizen who
 * reads "Up to ₹5,00,000" in one place and "Under ₹5,00,000" in another has been given
 * two different rules, so this is a single hook rather than three near-copies.
 *
 * Where each half comes from:
 *
 *   "Your profile"  the citizen's own profile field, named by the rule's `fields[0]`
 *   "Requirement"   the rule's published condition, negated — see `lib/ruleRequirement`,
 *                   which turns the *blocking* expression into the requirement it implies
 *   PASSED / not    this citizen's own match run, never recomputed here
 *
 * Nothing is inferred when the engine has not spoken: a rule that is neither in
 * `matched_because` nor in `blocked_because` renders as neither, because "we have not
 * checked this yet" and "you failed this" are different things to be told.
 */

import { useTranslations } from "next-intl";

import { criterionKey } from "@/components/account/criteriaLabels";
import { formatRupees } from "@/lib/format";
import { isMoneyField, requirementFrom, type RequirementOp } from "@/lib/ruleRequirement";

import type { MatchResult } from "@/lib/api";
import type { CitizenProfile, SchemeRule } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

/** How a requirement operator reads. `schemeDetail.req*` supplies the wording. */
const OP_KEY: Record<RequirementOp, string> = {
  eq: "reqIs",
  ne: "reqIsNot",
  lte: "reqUpTo",
  lt: "reqUnder",
  gte: "reqAtLeast",
  gt: "reqOver",
};

/** Operators that state a numeric bound, so a failed row can be drawn as two bars. */
const BOUNDS: Partial<Record<RequirementOp, "ceiling" | "floor">> = {
  lte: "ceiling",
  lt: "ceiling",
  gte: "floor",
  gt: "floor",
};

export interface CriterionRow {
  /** The criterion, not the rule — several rules can share one. */
  key: string;
  label: string;
  passed: boolean;
  failed: boolean;
  /** Already formatted and localised. */
  yours: string;
  /** One entry per rule behind this criterion, so a band reads as its two bounds. */
  required: string[];
  ruleIds: string[];
  /**
   * The numbers behind a *failed* numeric criterion, for the comparison bars. Null unless
   * the citizen's value and the rule's bound are both numbers — there is no honest bar to
   * draw for "your category is OBC, the rule wants SC".
   */
  gap: { yours: number; limit: number; kind: "ceiling" | "floor" } | null;
}

export function useCriteriaRows(
  rules: SchemeRule[] | undefined,
  mine: MatchResult | null | undefined,
  profile: CitizenProfile | null | undefined,
  locale: Locale,
): CriterionRow[] {
  const t = useTranslations("schemeDetail");
  const tCommon = useTranslations("common");

  const raw = (field: string): unknown =>
    profile ? profile[field as keyof CitizenProfile] : undefined;

  /** How a profile value reads. `null` is not "no" — it is "not answered yet", and the
   *  row says so rather than implying a value the citizen never gave. */
  const profileValue = (field: string): string => {
    const value = raw(field);
    if (value === null || value === undefined) return t("notAnswered");
    if (typeof value === "boolean") return value ? t("yes") : t("no");
    if (typeof value === "number") {
      return isMoneyField(field)
        ? tCommon("rupees", { amount: formatRupees(value, locale) })
        : String(value);
    }
    // Category and sector codes are shown verbatim — they are what the engine matched on
    // and what a partner's own form will ask for.
    return String(value);
  };

  const rows: CriterionRow[] = [];

  for (const rule of (rules ?? []).filter((r) => r.severity === "HARD_BLOCK")) {
    const requirement = requirementFrom(rule.when_source);
    const field = rule.fields[0] ?? "";
    const key = criterionKey(rule.rule_id) ?? rule.rule_id;
    const passed = mine?.matched_because.some((r) => r.rule_id === rule.rule_id) ?? false;
    const failed = mine?.blocked_because.some((r) => r.rule_id === rule.rule_id) ?? false;

    let required: string | null = null;
    if (requirement) {
      const value =
        typeof requirement.value === "boolean"
          ? requirement.value
            ? t("yes")
            : t("no")
          : typeof requirement.value === "number" && isMoneyField(requirement.field)
            ? tCommon("rupees", { amount: formatRupees(requirement.value, locale) })
            : String(requirement.value);
      required = t(OP_KEY[requirement.op], { value });
    }

    // Only a failed rule gets bars, and only when both sides are real numbers.
    const yoursRaw = raw(field);
    const kind = requirement ? BOUNDS[requirement.op] : undefined;
    const gap =
      failed &&
      kind &&
      typeof yoursRaw === "number" &&
      typeof requirement?.value === "number"
        ? { yours: yoursRaw, limit: requirement.value, kind }
        : null;

    const existing = rows.find((row) => row.key === key);
    if (existing) {
      // Several rules can bear on one criterion — a Term Loan brackets project cost with
      // a floor and a ceiling — and the design draws one row per criterion. The row only
      // ticks if every rule behind it passed; merging the other way would tick a row that
      // half failed.
      existing.passed = existing.passed && passed;
      existing.failed = existing.failed || failed;
      if (required && !existing.required.includes(required)) existing.required.push(required);
      existing.ruleIds.push(rule.rule_id);
      existing.gap = existing.gap ?? gap;
      continue;
    }

    rows.push({
      key,
      label: criterionKey(rule.rule_id) ? t(`criterion.${key}`) : rule.message,
      passed,
      failed,
      yours: field ? profileValue(field) : tCommon("notApplicable"),
      required: required ? [required] : [],
      ruleIds: [rule.rule_id],
      gap,
    });
  }

  return rows;
}
