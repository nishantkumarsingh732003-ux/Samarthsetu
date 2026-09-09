import { getTranslations } from "next-intl/server";

import { formatRupees } from "@/lib/format";
import { SCHEME_FACTS } from "@/lib/schemeFacts";

import type { Locale } from "@/i18n/config";

/**
 * The three schemes, rendered on the server from the rule pack.
 *
 * The design drop's cards named NBCFDC, SIDBI and Stand-Up India products with rates
 * beside them. This repository's rule pack covers the three NSFDC families the problem
 * statement actually names, and every figure in it carries a `source_url` and a
 * `last_verified_on` — which is why each card prints the verification date rather than
 * quoting a rate from nowhere. Adding a scheme here means adding sourced YAML to
 * `packages/rules`, not adding copy.
 *
 * Names are verbatim. CLAUDE.md forbids machine-translating a legal scheme name: a
 * citizen has to be able to say, at the counter, the name the counter knows.
 */

const SUMMARY_KEY = {
  MICRO_FINANCE: "schemeMicroSummary",
  TERM_LOAN: "schemeTermSummary",
  EDUCATION_LOAN: "schemeEducationSummary",
} as const;

export async function FeaturedSchemes({ locale }: { locale: Locale }) {
  const t = await getTranslations();

  return (
    <ul className="grid grid-cols-1 gap-4 md:grid-cols-3">
      {SCHEME_FACTS.map((scheme) => {
        // The Educational Loan Scheme states no project ceiling, only a loan cap, so its
        // card quotes the cap. Reading `?? maxLoanAmount` blindly would silently print a
        // project ceiling that scheme does not have.
        const cap =
          scheme.family === "EDUCATION_LOAN" ? scheme.maxLoanAmount : scheme.maxProjectCost;

        return (
          <li key={scheme.code} className="panel flex flex-col p-5">
            <span className="chip w-fit bg-accent-50 text-accent-800">{scheme.agency}</span>

            <h3 className="mt-3.5 font-display text-lg font-bold" lang="en">
              {scheme.officialName}
            </h3>
            <p className="mt-1.5 text-ink-muted">
              {t(`landing.${SUMMARY_KEY[scheme.family]}`, {
                cap: t("common.rupees", { amount: formatRupees(cap ?? 0, locale) }),
              })}
            </p>

            <div className="mt-4 flex items-baseline justify-between gap-3 border-t border-line pt-3.5">
              <span className="text-ink-faint">{t("landing.schemeRate")}</span>
              <span className="numeric font-display text-base font-bold">
                {t("landing.schemeRateValue", { rate: scheme.interestRate })}
              </span>
            </div>
            <p className="mt-2 text-sm text-ink-faint">
              {t("landing.schemeSource", { date: scheme.lastVerifiedOn })}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
