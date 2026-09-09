"use client";

/**
 * Every scheme in the rule pack, whether or not this citizen qualifies for it.
 *
 * This is the catalogue, not the recommendation — /matches is the recommendation. The
 * distinction matters because someone whose income is above the ceiling this year should
 * still be able to read what the scheme offers, and someone helping a relative should be
 * able to look up terms without filling in a profile at all. The endpoint behind it needs
 * no login for the same reason.
 *
 * The "some figures unverified" chip is not a hedge. It comes from the rule pack's own
 * provenance block, and clicking through shows exactly which figures and what question
 * is still open against each.
 */

import { AlertTriangle, ChevronRight } from "lucide-react";
import { useTranslations } from "next-intl";

import { useCatalogue } from "@/components/account/useCitizenData";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { Locale } from "@/i18n/config";

export function CatalogueClient({ locale }: { locale: Locale }) {
  const t = useTranslations("schemeCatalogue");
  const tCommon = useTranslations("common");
  const { data, loading } = useCatalogue(locale);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
        </div>
        <Link href="/compare" className="btn-secondary text-base">
          {t("compare")}
        </Link>
      </header>

      {loading && !data ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : (
        <ul className="grid gap-4 lg:grid-cols-2">
          {(data?.schemes ?? []).map((scheme) => (
            <li key={scheme.code}>
              <Link href={`/schemes/${scheme.code}`} className="panel-link h-full p-5">
                <div className="flex flex-wrap items-center gap-2">
                  <Chip tone="accent">{scheme.family.replace(/_/g, " ")}</Chip>
                  {scheme.provenance.needs_verification && (
                    <Chip tone="warn">
                      <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                      {t("unverified")}
                    </Chip>
                  )}
                </div>

                {/* Official name verbatim; the gloss below is a transliteration aid. */}
                <h2 className="mt-3 font-display text-lg font-bold">{scheme.official_name}</h2>
                {scheme.name_gloss && (
                  <p className="mt-0.5 text-ink-muted">{scheme.name_gloss}</p>
                )}

                {/* Two different quantities, both named.
                    The loan is what NSFDC advances; the project cost is what the scheme
                    covers, and it is the figure the problem statement quotes — ₹1,40,000
                    for Micro Finance, ₹50,00,000 for the Term Loan. Printing only the
                    loan under a bare "Up to" made the card look like it contradicted the
                    scheme: Micro Finance read ₹1,25,000 where the PS says ₹1,40,000. It
                    never did; 90% of ₹1,40,000 is the loan. Now the card says so. */}
                <p className="numeric mt-3 text-lg font-semibold text-accent-700">
                  {scheme.limits.max_loan_amount !== null
                    ? t("loanUpTo", {
                        amount: formatRupees(scheme.limits.max_loan_amount, locale),
                      })
                    : tCommon("notApplicable")}
                </p>
                <p className="numeric mt-0.5 text-sm text-ink-muted">
                  {scheme.limits.max_project_cost !== null
                    ? t("projectUpTo", {
                        amount: formatRupees(scheme.limits.max_project_cost, locale),
                      })
                    : t("projectAny")}
                </p>

                <p className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-faint">
                  <span>{t("rules", { count: scheme.rule_count })}</span>
                  <span aria-hidden="true">·</span>
                  <span>{t("partners", { count: scheme.authorised_partner_count })}</span>
                </p>

                <span className="mt-4 inline-flex items-center gap-1 font-medium text-accent-700">
                  {t("openScheme")}
                  <ChevronRight className="h-4 w-4" aria-hidden="true" />
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
