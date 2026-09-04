import { describe, expect, it } from "vitest";

import { amortisationByYear, maxAdvance, repaymentPlan } from "./emi";

describe("repaymentPlan", () => {
  it("matches the standard EMI formula", () => {
    // ₹9,00,000 at 8% over 7 years. Cross-checked against the closed form
    // P·r·(1+r)^n / ((1+r)^n − 1) with r = 0.08/12, n = 84, which gives 14027.592962.
    const plan = repaymentPlan(900000, 8, 84);
    expect(plan.emi).toBeCloseTo(14027.5929, 3);
    expect(plan.totalInterest).toBeCloseTo(278317.81, 1);
    expect(plan.totalPayment).toBeCloseTo(plan.emi * 84, 6);
    expect(plan.totalInterest).toBeCloseTo(plan.totalPayment - 900000, 6);
  });

  it("does not divide by zero at 0% interest", () => {
    const plan = repaymentPlan(120000, 0, 24);
    expect(plan.emi).toBe(5000);
    expect(plan.totalInterest).toBe(0);
    expect(plan.moratoriumInterest).toBe(0);
  });

  it("capitalises interest accrued during a moratorium", () => {
    // The design drop accepted a moratorium and then ignored it, which understates the
    // total repaid. A holiday from paying is not a holiday from interest.
    const without = repaymentPlan(900000, 8, 84, 0);
    const withHoliday = repaymentPlan(900000, 8, 84, 6);

    expect(withHoliday.moratoriumInterest).toBeGreaterThan(0);
    expect(withHoliday.emi).toBeGreaterThan(without.emi);
    expect(withHoliday.totalInterest).toBeGreaterThan(without.totalInterest);
    // Six months at 8% compounds the principal by (1 + 0.08/12)^6.
    expect(withHoliday.amortisedPrincipal).toBeCloseTo(900000 * (1 + 0.08 / 12) ** 6, 4);
  });

  it("returns an empty plan rather than NaN for nonsense input", () => {
    for (const plan of [
      repaymentPlan(0, 8, 84),
      repaymentPlan(-5, 8, 84),
      repaymentPlan(900000, 8, 0),
    ]) {
      expect(plan.emi).toBe(0);
      expect(Number.isNaN(plan.totalPayment)).toBe(false);
    }
  });

  it("treats a negative rate as zero rather than paying the borrower", () => {
    expect(repaymentPlan(120000, -5, 24).emi).toBe(5000);
  });
});

describe("amortisationByYear", () => {
  it("fully repays the loan by the last instalment", () => {
    const plan = repaymentPlan(900000, 8, 84);
    const years = amortisationByYear(plan, 8);

    expect(years).toHaveLength(7);
    expect(years.at(-1)!.closingBalance).toBe(0);

    const principal = years.reduce((sum, year) => sum + year.principal, 0);
    // Within a rupee of the amortised principal after rounding each year.
    expect(Math.abs(principal - plan.amortisedPrincipal)).toBeLessThan(2);
  });

  it("front-loads interest, as an amortising loan does", () => {
    const plan = repaymentPlan(900000, 8, 84);
    const years = amortisationByYear(plan, 8);
    expect(years[0].interest).toBeGreaterThan(years.at(-1)!.interest);
    expect(years[0].principal).toBeLessThan(years.at(-1)!.principal);
  });

  it("has nothing to show for an empty plan", () => {
    expect(amortisationByYear(repaymentPlan(0, 8, 84), 8)).toEqual([]);
  });
});

describe("maxAdvance", () => {
  it("takes the smaller of the percentage and the cash cap", () => {
    // NSFDC Micro Finance: 90% of a ₹1,40,000 project is ₹1,26,000, but the scheme
    // advances at most ₹1,25,000. Quoting the percentage alone overstates it.
    expect(maxAdvance(140000, 90, 125000)).toBe(125000);
  });

  it("uses the percentage when it is the binding limit", () => {
    expect(maxAdvance(100000, 90, 125000)).toBe(90000);
  });

  it("copes with either ceiling being unpublished", () => {
    expect(maxAdvance(100000, 90, null)).toBe(90000);
    expect(maxAdvance(100000, null, 125000)).toBe(125000);
    expect(maxAdvance(100000, null, null)).toBeNull();
  });

  it("never returns a fraction of a rupee", () => {
    expect(Number.isInteger(maxAdvance(133333, 90, null)!)).toBe(true);
  });
});
