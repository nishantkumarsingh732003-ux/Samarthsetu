"use client";

/**
 * Schemes side by side, drawn to the SamarthSetu design drop.
 *
 * The citizen's own standing is the first thing in the table, and that is the reason this
 * page exists. Comparing published terms alone invites the wrong conclusion — the Term
 * Loan offers far more money than the Micro Finance Scheme, so it always looks better,
 * right up until a hard-block rule makes it unavailable to *this* applicant. Terms and
 * eligibility have to be read together, so the profile match and the verdict sit above
 * every figure they would otherwise be compared without.
 *
 * Two rows the drop does not have, both kept because leaving them out would mislead:
 *
 *   Maximum loan   the rule pack states two ceilings, not one. NSFDC will fund a unit
 *                  costing up to Rs 1,40,000 but will only advance Rs 1,25,000 against
 *                  it — see the header comment in micro_finance.yaml. A table with only
 *                  "project limit" overstates what a citizen can borrow, which is the
 *                  exact misreading that file was written to prevent.
 *   Your verdict   a 100% profile match is a ranking score, not permission. The verdict
 *                  is the permission, and it belongs next to the number people will read
 *                  as one.
 *
 * The drop's "Subsidy" row is not here. Nothing in the rule pack records a subsidy or an
 * interest subvention, and a column of invented percentages on a ministry-branded
 * comparison is worse than a missing row. "Share funded" takes the slot: it is the same
 * question — how much of this do I not have to find myself — and it is published.
 *
 * Document counts and eligible categories are not on the catalogue summary, so the three
 * chosen schemes are fetched in full. Three requests, only for the columns on screen, and
 * only when the selection changes.
 */

import { ArrowRight, Check, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { VerdictChip } from "@/components/account/MatchCard";
import { useCatalogue, useMatches } from "@/components/account/useCitizenData";
import { Chip } from "@/components/ui/controls";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { Link } from "@/i18n/navigation";
import { getScheme } from "@/lib/citizenApi";
import { formatRupees } from "@/lib/format";
import { requirementFrom } from "@/lib/ruleRequirement";
import { schemeFact } from "@/lib/schemeFacts";

import type { SchemeDetail, SchemeSummary } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

const MAX_CHOSEN = 3;

export function CompareClient({ locale }: { locale: Locale }) {
  const t = useTranslations("compare");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");

  const catalogue = useCatalogue(locale);
  const matches = useMatches(locale);
  const [chosen, setChosen] = useState<string[] | null>(null);
  const [details, setDetails] = useState<Record<string, SchemeDetail>>({});

  const schemes = catalogue.data?.schemes ?? [];
  // Default to the first three in the catalogue until the citizen picks; `null` means
  // "not chosen yet" so an explicit empty selection is not overwritten on every render.
  const selected = chosen ?? schemes.slice(0, MAX_CHOSEN).map((scheme) => scheme.code);
  const columns = schemes.filter((scheme) => selected.includes(scheme.code));

  /** Full detail for the chosen columns only. Anything already fetched is kept, so
   *  deselecting and reselecting a scheme costs nothing. */
  useEffect(() => {
    let cancelled = false;
    for (const code of selected) {
      if (details[code]) continue;
      void getScheme(code, locale).then((result) => {
        if (cancelled || !result.ok) return;
        setDetails((current) => ({ ...current, [code]: result.data }));
      });
    }
    return () => {
      cancelled = true;
    };
    // `selected` is a fresh array each render; its contents are the real dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected.join(","), locale]);

  const dash = tCommon("notApplicable");
  const money = (value: number | null) =>
    value === null ? dash : tCommon("rupees", { amount: formatRupees(value, locale) });
  const years = (value: number | null) =>
    value === null ? dash : tMatches("upToYears", { years: Math.round(value / 12) });
  const months = (value: number | null) =>
    value === null ? dash : tMatches("upToMonths", { count: value });

  const resultFor = (code: string) =>
    matches.data?.results.find((result) => result.scheme_code === code) ?? null;

  const fitFor = (code: string) => {
    const mine = resultFor(code);
    return mine?.fit ? Math.round(mine.fit.total) : null;
  };

  /**
   * The best fit among the chosen columns, which is the one that gets the chip and the
   * tinted column. A blocked scheme never wins it, however high it scores: the score
   * orders the list, the verdict decides whether it is on the table at all.
   */
  const bestFit = columns
    .filter((scheme) => resultFor(scheme.code)?.verdict !== "INELIGIBLE")
    .reduce<{ code: string; fit: number } | null>((best, scheme) => {
      const fit = fitFor(scheme.code);
      if (fit === null) return best;
      return best === null || fit > best.fit ? { code: scheme.code, fit } : best;
    }, null);

  /**
   * Which categories a scheme admits, read off its own category rule rather than written
   * down again here. `profile.category != 'SC'` blocks, so the requirement is `SC` — see
   * lib/ruleRequirement, which negates the blocking condition.
   */
  const categoriesFor = (code: string): string => {
    const rules = details[code]?.rules;
    if (!rules) return dash;
    const values = rules
      .filter((rule) => rule.fields.includes("category"))
      .map((rule) => requirementFrom(rule.when_source))
      .filter((requirement) => requirement?.op === "eq")
      .map((requirement) => String(requirement!.value));
    return values.length > 0 ? values.join(", ") : dash;
  };

  const rows: { label: string; cell: (scheme: SchemeSummary) => React.ReactNode }[] = [
    {
      label: t("profileMatch"),
      cell: (scheme) => {
        const fit = fitFor(scheme.code);
        return fit === null ? (
          dash
        ) : (
          <span
            className={`numeric font-bold ${fit >= 80 ? "text-good-fg" : "text-ink"}`}
          >
            {fit}%
          </span>
        );
      },
    },
    {
      label: t("yourVerdict"),
      cell: (scheme) => {
        const mine = resultFor(scheme.code);
        return mine ? <VerdictChip verdict={mine.verdict} /> : dash;
      },
    },
    { label: t("projectLimit"), cell: (s) => money(s.limits.max_project_cost) },
    { label: t("maxLoan"), cell: (s) => money(s.limits.max_loan_amount) },
    {
      label: t("interest"),
      cell: (s) =>
        s.limits.interest_rate_min === null
          ? dash
          : s.limits.interest_rate_min === s.limits.interest_rate_max
            ? tMatches("perYearFlat", { rate: s.limits.interest_rate_min })
            : tMatches("perYear", {
                min: s.limits.interest_rate_min,
                max: s.limits.interest_rate_max,
              }),
    },
    { label: t("tenure"), cell: (s) => years(s.limits.tenure_months) },
    { label: t("moratorium"), cell: (s) => months(s.limits.moratorium_months) },
    {
      label: t("fundingPct"),
      cell: (s) => (s.limits.max_funding_pct === null ? dash : `${s.limits.max_funding_pct}%`),
    },
    {
      label: t("documents"),
      cell: (s) => {
        const count = details[s.code]?.required_documents.length;
        return count === undefined ? dash : t("documentsCount", { count });
      },
    },
    { label: t("categories"), cell: (s) => categoriesFor(s.code) },
    { label: t("partners"), cell: (s) => s.authorised_partner_count },
  ];

  /** The tint the best-fit column carries all the way down. */
  const columnTone = (code: string) => (bestFit?.code === code ? "bg-good-bg/30" : "");

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      <section className="panel p-4 lg:p-5">
        <h2 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
          {t("pick")}
        </h2>
        <ToggleGroup
          type="multiple"
          value={selected}
          // Radix hands back the whole next selection. The cap is enforced here rather
          // than by disabling, so a citizen who has three can still *deselect* one from
          // the group — a disabled item cannot be un-pressed.
          onValueChange={(next: string[]) =>
            setChosen(next.length <= MAX_CHOSEN ? next : selected)
          }
          className="mt-3"
        >
          {schemes.map((scheme) => {
            const on = selected.includes(scheme.code);
            return (
              <ToggleGroupItem
                key={scheme.code}
                value={scheme.code}
                disabled={!on && selected.length >= MAX_CHOSEN}
                aria-label={scheme.official_name}
              >
                {on && <Check className="h-4 w-4 shrink-0" aria-hidden="true" />}
                <span lang="en">{scheme.official_name}</span>
              </ToggleGroupItem>
            );
          })}
        </ToggleGroup>
        {selected.length >= MAX_CHOSEN && (
          <p className="mt-3 text-sm text-ink-faint">{t("limitReached")}</p>
        )}
      </section>

      {columns.length === 0 ? (
        <p className="panel p-8 text-center text-ink-faint">{t("noneChosen")}</p>
      ) : (
        <div className="panel overflow-hidden">
          <Table>
            <TableCaption>{t("title")}</TableCaption>
            <TableHeader>
              <TableRow className="border-b border-line bg-canvas">
                <TableHead
                  scope="col"
                  className="w-52 text-xs font-bold uppercase tracking-widest text-ink-faint"
                >
                  {t("feature")}
                </TableHead>
                {columns.map((scheme) => (
                  <TableHead
                    key={scheme.code}
                    scope="col"
                    className={`border-l border-line ${columnTone(scheme.code)}`}
                  >
                    <span className="flex flex-wrap items-center gap-2">
                      {/* Official name verbatim, never machine-translated (CLAUDE.md). */}
                      <span className="font-display text-lg font-bold text-ink" lang="en">
                        {scheme.official_name}
                      </span>
                      {bestFit?.code === scheme.code && (
                        <Chip tone="good">
                          <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                          {t("bestFit")}
                        </Chip>
                      )}
                    </span>
                    <span className="mt-0.5 block text-sm font-normal text-ink-faint">
                      {schemeFact(scheme.code)?.agency ?? scheme.family.replace(/_/g, " ")}
                    </span>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {rows.map((row) => (
                <TableRow key={row.label}>
                  <TableHead scope="row" className="align-middle">
                    {row.label}
                  </TableHead>
                  {columns.map((scheme) => (
                    <TableCell
                      key={scheme.code}
                      className={`border-l border-line/70 tabular-nums ${columnTone(scheme.code)}`}
                    >
                      {row.cell(scheme)}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
              <TableRow className="border-b-0">
                <TableCell />
                {columns.map((scheme) => (
                  <TableCell
                    key={scheme.code}
                    className={`border-l border-line/70 ${columnTone(scheme.code)}`}
                  >
                    <Link
                      href={`/schemes/${scheme.code}`}
                      className="btn-primary rounded-full text-base"
                    >
                      {t("open")}
                      <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </Link>
                  </TableCell>
                ))}
              </TableRow>
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
