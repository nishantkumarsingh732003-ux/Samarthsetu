/**
 * Every rule in the published pack must yield a requirement, and the requirement must be
 * the negation of the condition — not the condition itself.
 *
 * The second half is the one that matters. `annual_family_income > 500000` blocks, so the
 * requirement is "up to 5,00,000"; an off-by-one-negation bug would print that ceiling as
 * a floor on the eligibility row and tell a citizen the opposite of the rule. That is not
 * a rendering bug, it is wrong advice about government credit, so it is pinned here
 * against the real pack rather than against fixtures.
 */

import { readFileSync } from "node:fs";
import { join } from "node:path";

import { describe, expect, it } from "vitest";

import { isMoneyField, requirementFrom } from "./ruleRequirement";

const RULES = join(__dirname, "..", "..", "..", "..", "packages", "rules", "dist", "rules.json");

interface RulePack {
  schemes: { rules: { id: string; when_source: string }[] }[];
}

function packRules() {
  const pack = JSON.parse(readFileSync(RULES, "utf8")) as RulePack;
  return pack.schemes.flatMap((scheme) => scheme.rules);
}

describe("requirementFrom", () => {
  it("parses every rule in the published pack", () => {
    const unparsed = packRules()
      .filter((rule) => requirementFrom(rule.when_source) === null)
      .map((rule) => `${rule.id}: ${rule.when_source}`);
    expect(unparsed).toEqual([]);
  });

  it("negates the blocking condition rather than repeating it", () => {
    // A ceiling that blocks above 5,00,000 is a requirement of "at most 5,00,000".
    expect(requirementFrom("profile.annual_family_income > 500000")).toEqual({
      field: "annual_family_income",
      op: "lte",
      value: 500000,
    });
    // A floor that blocks at or below 1,40,000 is a requirement of "more than 1,40,000".
    expect(requirementFrom("profile.project_cost <= 140000")).toEqual({
      field: "project_cost",
      op: "gt",
      value: 140000,
    });
    // Blocking everyone who is not SC is a requirement of being SC.
    expect(requirementFrom("profile.category != 'SC'")).toEqual({
      field: "category",
      op: "eq",
      value: "SC",
    });
    // Blocking education projects is a requirement of not being one.
    expect(requirementFrom("profile.project_sector == 'EDUCATION'")).toEqual({
      field: "project_sector",
      op: "ne",
      value: "EDUCATION",
    });
    // Booleans come through as booleans, not as the strings "true"/"false".
    expect(requirementFrom("profile.admission_confirmed == false")).toEqual({
      field: "admission_confirmed",
      op: "ne",
      value: false,
    });
  });

  it("refuses anything that is not a single comparison", () => {
    expect(requirementFrom("profile.a > 1 and profile.b < 2")).toBeNull();
    expect(requirementFrom("len(profile.documents) > 0")).toBeNull();
    expect(requirementFrom("profile.category")).toBeNull();
  });

  it("knows which profile fields are money", () => {
    expect(isMoneyField("annual_family_income")).toBe(true);
    expect(isMoneyField("project_cost")).toBe(true);
    expect(isMoneyField("category")).toBe(false);
    expect(isMoneyField("admission_confirmed")).toBe(false);
  });
});
