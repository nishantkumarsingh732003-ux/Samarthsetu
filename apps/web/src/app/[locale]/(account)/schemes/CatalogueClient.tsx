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

import type { SchemeSummary } from "@/lib/citizenApi";

import type { Locale } from "@/i18n/config";

export function CatalogueClient({ locale }: { locale: Locale }) {
  const t = useTranslations("schemeCatalogue");
  const tCommon = useTranslations("common");
  const { data, loading } = useCatalogue(locale);

  /**
   * The four figures a scheme card shows, in the shape the match cards use.
   *
   * Built here rather than inline so the card body stays a layout. Interest collapses to
   * one number when the band has no width — every scheme currently quotes a single rate,
   * and "6.5–6.5%" is noise.
   */
  const figuresFor = (scheme: SchemeSummary): { label: string; value: string }[] => {
    const limits = scheme.limits;
    const rupees = (amount: number) =>
      tCommon("rupees", { amount: formatRupees(amount, locale) });

    const figures: { label: string; value: string }[] = [];

    if (limits.max_loan_amount !== null) {
      figures.push({ label: t("labelLoan"), value: rupees(limits.max_loan_amount) });
    }
    figures.push({
      label: t("labelProject"),
      value:
        limits.max_project_cost !== null
          ? rupees(limits.max_project_cost)
          : t("projectAny"),
    });
    if (limits.interest_rate_min !== null) {
      const { interest_rate_min: lo, interest_rate_max: hi } = limits;
      figures.push({
        label: t("labelInterest"),
        value:
          hi !== null && hi !== lo
            ? t("interestBand", { min: lo, max: hi })
            : t("interestFlat", { rate: lo }),
      });
    }
    if (limits.max_funding_pct !== null) {
      figures.push({ label: t("labelFunding"), value: `${limits.max_funding_pct}%` });
    }
    return figures.slice(0, 4);
  };

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

                {/* The same labelled stat grid the match cards use.
                    Two things were wrong before. The figure was set in `numeric`, which
                    is `font-mono` — reserved for reference numbers you read down a phone
                    line — so a loan amount rendered as code. And it was a bare "Up to
                    ₹1,25,000" with no noun, which read as the scheme's ceiling and so
                    looked like it contradicted the problem statement's ₹1,40,000 for
                    Micro Finance. They are different quantities: ₹1,40,000 is the project
                    cost the scheme covers, ₹1,25,000 the loan advanced against it, and
                    90% of the one is the other. Both are named and both are shown. */}
                <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-4">
                  {figuresFor(scheme).map((figure) => (
                    <div key={figure.label} className="flex flex-col">
                      <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-ink-faint">
                        {figure.label}
                      </dt>
                      <dd className="mt-auto pt-1.5 font-semibold tabular-nums">
                        {figure.value}
                      </dd>
                    </div>
                  ))}
                </dl>

                <p className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-ink-faint">
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
