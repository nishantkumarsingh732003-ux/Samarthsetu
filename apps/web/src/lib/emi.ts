/**
 * Repayment arithmetic for the planning screen.
 *
 * Pure functions with no React and no formatting, so they are testable on their own —
 * which matters more here than usual. A citizen deciding whether they can afford a
 * ₹9,00,000 term loan is making the largest financial decision of their year on the
 * number this file returns.
 *
 * Three things it is careful about, because the design drop got two of them wrong:
 *
 * 1. **Zero interest does not divide by zero.** The standard EMI formula has `r` in the
 *    denominator; at 0% it is `P / n`.
 *
 * 2. **A moratorium is not free.** During the moratorium the borrower pays nothing but
 *    interest still accrues on the outstanding principal, and NSFDC capitalises it. The
 *    drop's calculator accepted a moratorium input and then ignored it, which understates
 *    the total repaid — the direction of error that matters.
 *
 * 3. **Nothing here is an offer.** These are indicative figures from published rates.
 *    The sanctioning partner sets the actual terms, and the UI says so beside every
 *    number this produces.
 */

export interface RepaymentPlan {
  /** Level monthly instalment once repayment starts, in rupees. */
  emi: number;
  /** Principal actually amortised — the loan plus interest capitalised during the
   *  moratorium, which is what the instalments are calculated on. */
  amortisedPrincipal: number;
  /** Interest accrued during the moratorium and added to the principal. */
  moratoriumInterest: number;
  totalInterest: number;
  totalPayment: number;
  months: number;
  moratoriumMonths: number;
}

export interface YearSlice {
  year: number;
  principal: number;
  interest: number;
  closingBalance: number;
}

/**
 * @param principal   amount borrowed, in rupees
 * @param annualRate  nominal annual rate as a percentage, e.g. 6.5
 * @param months      repayment period *after* the moratorium
 * @param moratoriumMonths  months before the first instalment falls due
 */
export function repaymentPlan(
  principal: number,
  annualRate: number,
  months: number,
  moratoriumMonths = 0,
): RepaymentPlan {
  const empty: RepaymentPlan = {
    emi: 0,
    amortisedPrincipal: 0,
    moratoriumInterest: 0,
    totalInterest: 0,
    totalPayment: 0,
    months: 0,
    moratoriumMonths: 0,
  };
  if (!(principal > 0) || !(months > 0)) return empty;

  const monthly = Math.max(annualRate, 0) / 12 / 100;
  const holdback = Math.max(moratoriumMonths, 0);

  // Interest accrues through the moratorium and is capitalised, so instalments are
  // calculated on a larger balance than was borrowed.
  const amortisedPrincipal = monthly === 0 ? principal : principal * (1 + monthly) ** holdback;
  const moratoriumInterest = amortisedPrincipal - principal;

  const emi =
    monthly === 0
      ? amortisedPrincipal / months
      : (amortisedPrincipal * monthly * (1 + monthly) ** months) /
        ((1 + monthly) ** months - 1);

  const totalPayment = emi * months;

  return {
    emi,
    amortisedPrincipal,
    moratoriumInterest,
    // Everything paid above what was borrowed, moratorium interest included.
    totalInterest: totalPayment - principal,
    totalPayment,
    months,
    moratoriumMonths: holdback,
  };
}

/**
 * Year-by-year split of principal and interest, for the repayment chart.
 *
 * The balance is carried forward month by month rather than approximated per year: an
 * annual approximation drifts by thousands of rupees over a seven-year term, and this
 * table is the one a citizen may hold beside a partner's own schedule.
 */
export function amortisationByYear(plan: RepaymentPlan, annualRate: number): YearSlice[] {
  if (plan.emi <= 0 || plan.months <= 0) return [];

  const monthly = Math.max(annualRate, 0) / 12 / 100;
  let balance = plan.amortisedPrincipal;
  const years: YearSlice[] = [];

  for (let year = 1; balance > 0.5 && year <= Math.ceil(plan.months / 12); year += 1) {
    let principalPaid = 0;
    let interestPaid = 0;
    const monthsThisYear = Math.min(12, plan.months - (year - 1) * 12);

    for (let month = 0; month < monthsThisYear; month += 1) {
      const interest = balance * monthly;
      // The final instalment cannot repay more than is outstanding.
      const principal = Math.min(plan.emi - interest, balance);
      balance -= principal;
      interestPaid += interest;
      principalPaid += principal;
    }

    years.push({
      year,
      principal: Math.round(principalPaid),
      interest: Math.round(interestPaid),
      closingBalance: Math.max(0, Math.round(balance)),
    });
  }

  return years;
}

/**
 * The largest loan a scheme will advance against a project of this size.
 *
 * Two ceilings apply and the smaller wins — which is the whole reason this is a function
 * and not a multiplication at the call site. NSFDC's Micro Finance Scheme allows 90% of
 * a project costing up to ₹1,40,000, but caps the advance at ₹1,25,000; 90% of the
 * ceiling is ₹1,26,000, so quoting the percentage alone overstates what a citizen can
 * actually borrow. Both figures come from the scheme's published limits.
 */
export function maxAdvance(
  projectCost: number,
  maxFundingPct: number | null,
  maxLoanAmount: number | null,
): number | null {
  const byPercentage =
    maxFundingPct !== null && projectCost > 0 ? (projectCost * maxFundingPct) / 100 : null;

  const candidates = [byPercentage, maxLoanAmount].filter(
    (value): value is number => value !== null && Number.isFinite(value),
  );
  return candidates.length === 0 ? null : Math.floor(Math.min(...candidates));
}
