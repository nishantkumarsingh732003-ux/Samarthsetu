/**
 * The landing page quotes scheme ceilings and rates without calling the API. This is
 * what stops those figures drifting away from the rule pack they came from.
 *
 * It reads `packages/rules/dist/rules.json` — the compiled pack the engine itself
 * loads — so a cap edited in YAML and rebuilt fails here rather than shipping a wrong
 * number to a citizen who is deciding whether to walk to a branch.
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { SCHEME_FACTS, TERM_LOAN_REPAYMENT, lastVerifiedOn } from "./schemeFacts";

const REPO = join(dirname(fileURLToPath(import.meta.url)), "..", "..", "..", "..");
const PACK = join(REPO, "packages", "rules", "dist", "rules.json");

interface PackScheme {
  code: string;
  official_name: string;
  family: string;
  limits: {
    max_loan_amount: number | null;
    max_project_cost: number | null;
    max_funding_pct: number | null;
    interest_rate_min: number | null;
    interest_rate_max: number | null;
    tenure_months: number | null;
    moratorium_months: number | null;
  };
  provenance: { source_url: string | null; last_verified_on: string | null };
}

const pack = JSON.parse(readFileSync(PACK, "utf8")) as { schemes: PackScheme[] };
const byCode = new Map(pack.schemes.map((scheme) => [scheme.code, scheme]));

describe("schemeFacts mirrors the rule pack", () => {
  it("covers every scheme in the pack, and invents none", () => {
    expect(SCHEME_FACTS.map((s) => s.code).sort()).toEqual(
      pack.schemes.map((s) => s.code).sort(),
    );
  });

  for (const fact of SCHEME_FACTS) {
    it(`${fact.code} matches`, () => {
      const scheme = byCode.get(fact.code);
      expect(scheme, `${fact.code} is not in the rule pack`).toBeDefined();
      if (!scheme) return;

      // Verbatim: CLAUDE.md forbids translating or paraphrasing a legal scheme name.
      expect(fact.officialName).toBe(scheme.official_name);
      expect(fact.family).toBe(scheme.family);

      expect(fact.maxLoanAmount).toBe(scheme.limits.max_loan_amount);
      expect(fact.maxProjectCost).toBe(scheme.limits.max_project_cost);
      expect(fact.maxFundingPct).toBe(scheme.limits.max_funding_pct);

      // The page shows one rate. It may only do that while the pack states one.
      expect(scheme.limits.interest_rate_min).toBe(scheme.limits.interest_rate_max);
      expect(fact.interestRate).toBe(scheme.limits.interest_rate_min);

      expect(fact.sourceUrl).toBe(scheme.provenance.source_url);
      expect(fact.lastVerifiedOn).toBe(scheme.provenance.last_verified_on);
    });
  }

  it("the worked example's repayment terms are the pack's Term Loan terms", () => {
    const termLoan = byCode.get("NSFDC_TERM_LOAN");
    expect(termLoan?.limits.tenure_months).toBe(TERM_LOAN_REPAYMENT.tenureMonths);
    expect(termLoan?.limits.moratorium_months).toBe(TERM_LOAN_REPAYMENT.moratoriumMonths);
  });

  it("reports a verification date the page can print", () => {
    expect(lastVerifiedOn()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
