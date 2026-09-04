"use client";

/**
 * Schemes side by side, with the citizen's own verdict as the first row.
 *
 * That row is the reason this page exists. Comparing published terms alone invites the
 * wrong conclusion — the Term Loan offers far more money than the Micro Finance Scheme,
 * so it always looks better, right up until a hard-block rule makes it unavailable to
 * this applicant. Terms and eligibility have to be read together.
 *
 * The table scrolls inside its own container rather than pushing the page sideways: a
 * horizontally scrolling body on a phone is how a citizen loses the navigation.
 */

import { useTranslations } from "next-intl";
import { useState } from "react";

import { VerdictChip } from "@/components/account/MatchCard";
import { useCatalogue, useMatches } from "@/components/account/useCitizenData";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { SchemeSummary } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

const MAX_CHOSEN = 3;

export function CompareClient({ locale }: { locale: Locale }) {
  const t = useTranslations("compare");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");

  const catalogue = useCatalogue(locale);
  const matches = useMatches(locale);
  const [chosen, setChosen] = useState<string[] | null>(null);

  const schemes = catalogue.data?.schemes ?? [];
  // Default to the first three in the catalogue until the citizen picks; `null` means
  // "not chosen yet" so an explicit empty selection is not overwritten on every render.
  const selected = chosen ?? schemes.slice(0, MAX_CHOSEN).map((scheme) => scheme.code);
  const columns = schemes.filter((scheme) => selected.includes(scheme.code));

  const toggle = (code: string) =>
    setChosen(
      selected.includes(code)
        ? selected.filter((value) => value !== code)
        : selected.length < MAX_CHOSEN
          ? [...selected, code]
          : selected,
    );

  const dash = tCommon("notApplicable");
  const money = (value: number | null) => (value === null ? dash : formatRupees(value, locale));
  const months = (value: number | null) =>
    value === null ? dash : tMatches("months", { count: value });

  const rows: { label: string; cell: (scheme: SchemeSummary) => React.ReactNode }[] = [
    {
      label: t("yourVerdict"),
      cell: (scheme) => {
        const mine = matches.data?.results.find(
          (result) => result.scheme_code === scheme.code,
        );
        return mine ? <VerdictChip verdict={mine.verdict} /> : dash;
      },
    },
    { label: t("maxLoan"), cell: (scheme) => money(scheme.limits.max_loan_amount) },
    { label: t("maxProject"), cell: (scheme) => money(scheme.limits.max_project_cost) },
    {
      label: t("fundingPct"),
      cell: (scheme) =>
        scheme.limits.max_funding_pct === null ? dash : `${scheme.limits.max_funding_pct}%`,
    },
    {
      label: t("interest"),
      cell: (scheme) =>
        scheme.limits.interest_rate_min === null
          ? dash
          : scheme.limits.interest_rate_min === scheme.limits.interest_rate_max
            ? tMatches("perYearFlat", { rate: scheme.limits.interest_rate_min })
            : tMatches("perYear", {
                min: scheme.limits.interest_rate_min,
                max: scheme.limits.interest_rate_max,
              }),
    },
    { label: t("tenure"), cell: (scheme) => months(scheme.limits.tenure_months) },
    { label: t("moratorium"), cell: (scheme) => months(scheme.limits.moratorium_months) },
    { label: t("rules"), cell: (scheme) => scheme.rule_count },
    { label: t("partners"), cell: (scheme) => scheme.authorised_partner_count },
  ];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      <section className="panel p-4">
        <h2 className="text-sm font-semibold text-ink-faint">{t("pick")}</h2>
        <ul className="mt-3 flex flex-wrap gap-2">
          {schemes.map((scheme) => {
            const on = selected.includes(scheme.code);
            const full = !on && selected.length >= MAX_CHOSEN;
            return (
              <li key={scheme.code}>
                <button
                  type="button"
                  aria-pressed={on}
                  disabled={full}
                  onClick={() => toggle(scheme.code)}
                  className={`min-h-touch rounded-full border-2 px-4 text-base font-medium transition-colors ${
                    on
                      ? "border-accent-700 bg-accent-700 text-white"
                      : full
                        ? "border-line text-ink-faint opacity-50"
                        : "border-line hover:border-accent-600"
                  }`}
                >
                  {scheme.official_name}
                </button>
              </li>
            );
          })}
        </ul>
        {selected.length >= MAX_CHOSEN && (
          <p className="mt-3 text-sm text-ink-faint">{t("limitReached")}</p>
        )}
      </section>

      {columns.length === 0 ? (
        <p className="panel p-8 text-center text-ink-faint">{t("noneChosen")}</p>
      ) : (
        <div className="panel overflow-x-auto">
          <table className="w-full min-w-[36rem] border-collapse text-left">
            <caption className="sr-only">{t("title")}</caption>
            <thead>
              <tr className="border-b border-line bg-canvas">
                <th scope="col" className="w-44 px-4 py-3 text-sm font-medium text-ink-faint">
                  {t("feature")}
                </th>
                {columns.map((scheme) => (
                  <th key={scheme.code} scope="col" className="border-l border-line px-4 py-3">
                    <span className="block font-display font-bold">
                      {scheme.official_name}
                    </span>
                    <span className="mt-0.5 block text-sm font-normal text-ink-faint">
                      {scheme.family.replace(/_/g, " ")}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label} className="border-b border-line/70">
                  <th scope="row" className="px-4 py-3 font-medium text-ink-muted">
                    {row.label}
                  </th>
                  {columns.map((scheme) => (
                    <td key={scheme.code} className="numeric border-l border-line/70 px-4 py-3">
                      {row.cell(scheme)}
                    </td>
                  ))}
                </tr>
              ))}
              <tr>
                <td className="px-4 py-3" />
                {columns.map((scheme) => (
                  <td key={scheme.code} className="border-l border-line/70 px-4 py-3">
                    <Link href={`/schemes/${scheme.code}`} className="btn-secondary text-base">
                      {t("open")}
                    </Link>
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
