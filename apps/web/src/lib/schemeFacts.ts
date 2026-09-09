/**
 * The headline figures the landing page quotes, mirrored from the rule pack.
 *
 * The landing page is the one screen a citizen sees before any API call has finished, so
 * the three scheme cards and the worked example are rendered on the server with no fetch
 * and no JavaScript. That means the numbers have to live somewhere in this app — and
 * CLAUDE.md rule 2 says no figure is written down without a source beside it.
 *
 * So every value here carries the same `sourceUrl` / `lastVerifiedOn` the YAML carries,
 * and `schemeFacts.test.ts` asserts the whole table against
 * `packages/rules/dist/rules.json`. If someone edits a scheme's cap or rate in the rule
 * pack and forgets this file, the test fails rather than the landing page quietly
 * telling a citizen the wrong ceiling.
 *
 * Names are NOT translated. CLAUDE.md: keep official scheme names verbatim and put the
 * transliterated gloss beside them — a citizen who walks into a branch has to say the
 * name the branch knows.
 */

export interface SchemeFact {
  /** The rule-pack code. Matches `packages/rules/schemes/*.yaml`. */
  code: string;
  /** Verbatim, never translated. */
  officialName: string;
  /** The corporation that runs the scheme, as it appears on the circular. */
  agency: string;
  family: "MICRO_FINANCE" | "TERM_LOAN" | "EDUCATION_LOAN";
  /** Rupees. The ceiling on what the scheme will advance. */
  maxLoanAmount: number;
  /** Rupees, or null where the scheme states no project ceiling. */
  maxProjectCost: number | null;
  /** Percent of project cost the scheme will fund. */
  maxFundingPct: number;
  /** Percent per annum. */
  interestRate: number;
  sourceUrl: string;
  lastVerifiedOn: string;
}

export const SCHEME_FACTS: readonly SchemeFact[] = [
  {
    code: "NSFDC_MICRO_FINANCE",
    officialName: "Micro Finance Scheme",
    agency: "NSFDC",
    family: "MICRO_FINANCE",
    maxLoanAmount: 125000,
    maxProjectCost: 140000,
    maxFundingPct: 90,
    interestRate: 6.5,
    sourceUrl: "https://nsfdc.nic.in/scheme",
    lastVerifiedOn: "2026-08-29",
  },
  {
    code: "NSFDC_TERM_LOAN",
    officialName: "Term Loan",
    agency: "NSFDC",
    family: "TERM_LOAN",
    maxLoanAmount: 4500000,
    maxProjectCost: 5000000,
    maxFundingPct: 90,
    interestRate: 8,
    sourceUrl: "https://nsfdc.nic.in/scheme",
    lastVerifiedOn: "2026-08-29",
  },
  {
    code: "NSFDC_EDUCATION_LOAN",
    officialName: "Educational Loan Scheme",
    agency: "NSFDC",
    family: "EDUCATION_LOAN",
    maxLoanAmount: 4000000,
    maxProjectCost: null,
    maxFundingPct: 90,
    interestRate: 6.5,
    sourceUrl: "https://nsfdc.nic.in/scheme",
    lastVerifiedOn: "2026-08-29",
  },
];

/**
 * The repayment terms the worked example on the landing page is computed from. Held
 * separately because only the Term Loan states a single tenure and moratorium the
 * engine can hold — the Educational Loan Scheme states two of each, and the rule pack
 * records null rather than picking one.
 */
export const TERM_LOAN_REPAYMENT = {
  tenureMonths: 84,
  moratoriumMonths: 6,
} as const;

export function schemeFact(code: string): SchemeFact | undefined {
  return SCHEME_FACTS.find((scheme) => scheme.code === code);
}

/** The newest `last_verified_on` across the table — what the page can honestly claim. */
export function lastVerifiedOn(): string {
  return SCHEME_FACTS.map((s) => s.lastVerifiedOn).sort().at(-1) ?? "";
}
