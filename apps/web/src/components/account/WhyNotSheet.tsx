"use client";

/**
 * "Why isn't this scheme recommended?" — the refusal, in the same side panel as its
 * opposite number.
 *
 * This is the screen the whole project exists for. A citizen turned away at a branch is
 * told "you are not eligible" and nothing else; here they get the criterion, the number
 * they gave, the number the rule wants, the arithmetic between them, and the scheme that
 * would have taken them instead. Every one of those is traceable to a rule id.
 *
 * The two bars are drawn only where they can be honest. A numeric bound — a ceiling or a
 * floor the citizen crossed — has a real gap to show, and showing it is worth more than
 * the sentence: ₹8,60,000 over the limit is a fact someone can act on, "project cost too
 * high" is not. A categorical rule ("this scheme is for Scheduled Caste applicants") has
 * no bar, so it does not get one; `useCriteriaRows` returns `gap: null` and the row falls
 * back to the plain comparison.
 *
 * The alternatives come from two places that must not contradict each other. The engine's
 * own `redirect_suggestion` is authoritative and goes first — it is the rule pack saying
 * "this applicant belongs in the Term Loan". Behind it come the other results in the same
 * run that the citizen actually qualifies for, in engine rank order. Nothing here is
 * ranked by this component.
 */

import { ArrowRight, TriangleAlert, X } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useCriteriaRows } from "@/components/account/useCriteriaRows";
import {
  Sheet,
  SheetBody,
  SheetContent,
  SheetDescription,
  SheetFooter,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Link } from "@/i18n/navigation";
import { getScheme } from "@/lib/citizenApi";
import { formatRupees } from "@/lib/format";

import type { MatchResult } from "@/lib/api";
import type { CitizenProfile, SchemeDetail } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export interface Alternative {
  code: string;
  name: string;
  agency: string | null;
  fit: number | null;
}

export function WhyNotSheet({
  open,
  onOpenChange,
  result,
  profile,
  alternatives,
  locale,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: MatchResult;
  profile: CitizenProfile | null | undefined;
  /** Other schemes in the same run the citizen qualifies for, in engine rank order. */
  alternatives: Alternative[];
  locale: Locale;
}) {
  const t = useTranslations("whyNotSheet");
  const tCommon = useTranslations("common");
  const [scheme, setScheme] = useState<SchemeDetail | null>(null);

  useEffect(() => {
    if (!open || scheme) return;
    let cancelled = false;
    void getScheme(result.scheme_code, locale).then((response) => {
      if (!cancelled && response.ok) setScheme(response.data);
    });
    return () => {
      cancelled = true;
    };
  }, [open, scheme, result.scheme_code, locale]);

  const rows = useCriteriaRows(scheme?.rules, result, profile, locale);
  const failed = rows.filter((row) => row.failed);

  // The first failed criterion with real numbers behind it. One chart, not four: the bars
  // are there to make a single gap concrete, and a stack of them is a table again.
  const gapRow = failed.find((row) => row.gap !== null);
  const gap = gapRow?.gap ?? null;
  const money = (value: number) =>
    tCommon("rupees", { amount: formatRupees(value, locale) });

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent closeLabel={tCommon("close")}>
        <SheetHeader>
          <SheetTitle>{t("title")}</SheetTitle>
          <SheetDescription className="mt-1.5" lang="en">
            {result.official_name}
          </SheetDescription>
        </SheetHeader>

        <SheetBody className="space-y-5">
          {!scheme ? (
            <p role="status" className="py-8 text-center text-ink-faint">
              {tCommon("loading")}
            </p>
          ) : (
            <>
              {gap && (
                <section>
                  {/* Both bars share one scale — the larger of the two values — so their
                      lengths are comparable. Scaling each to its own width would draw two
                      full bars and show nothing. */}
                  {[
                    {
                      // Mid-sentence, so the criterion is lowercased the way it would be
                      // written — `toLocaleLowerCase` because Turkish-style locales exist
                      // and `toLowerCase` gets them wrong.
                      label: t("yourValue", {
                        criterion: gapRow!.label.toLocaleLowerCase(locale),
                      }),
                      value: gap.yours,
                      tone: "bg-accent-700",
                    },
                    { label: t("schemeLimit"), value: gap.limit, tone: "bg-saffron" },
                  ].map((bar) => (
                    <div key={bar.label} className="mt-3 first:mt-0">
                      <div className="flex items-baseline justify-between gap-3">
                        <span className="text-sm text-ink-muted">{bar.label}</span>
                        <span className="numeric font-semibold">{money(bar.value)}</span>
                      </div>
                      <div className="mt-1.5 h-2.5 overflow-hidden rounded-full bg-canvas">
                        <div
                          className={`h-full rounded-full ${bar.tone}`}
                          style={{
                            width: `${(bar.value / Math.max(gap.yours, gap.limit)) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                  ))}

                  <p className="mt-4 rounded-card border border-saffron-line bg-saffron-bg px-4 py-3 text-saffron-fg">
                    {t(gap.kind === "ceiling" ? "differenceOver" : "differenceUnder", {
                      amount: money(Math.abs(gap.yours - gap.limit)),
                      criterion: gapRow!.label.toLocaleLowerCase(locale),
                    })}
                  </p>
                </section>
              )}

              <section>
                <h3 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                  {t("criteriaNotMet")}
                </h3>
                <ul className="mt-3 space-y-2.5">
                  {failed.map((row) => (
                    <li
                      key={row.key}
                      title={row.ruleIds.join(", ")}
                      className="rounded-card border border-stop-line bg-stop-bg/40 p-4"
                    >
                      <p className="flex items-center gap-2.5 font-semibold">
                        <X className="h-4 w-4 shrink-0 text-stop-fg" aria-hidden="true" />
                        {row.label}
                      </p>
                      <p className="mt-1 pl-7 text-sm text-ink-muted">
                        {t("yourProfile")}{" "}
                        <strong className="font-semibold text-ink">{row.yours}</strong>
                        {row.required.length > 0 && (
                          <>
                            {" · "}
                            {t("requirement")}{" "}
                            <strong className="font-semibold text-ink">
                              {row.required.join(" · ")}
                            </strong>
                          </>
                        )}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>

              {alternatives.length > 0 && (
                <section>
                  <h3 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                    {t("tryAlternatives")}
                  </h3>
                  <ul className="mt-3 space-y-2.5">
                    {alternatives.map((alternative) => (
                      <li key={alternative.code}>
                        <Link
                          href={`/schemes/${alternative.code}`}
                          className="panel lift flex items-center gap-3 p-4 transition-transform duration-200 ease-out hover:-translate-y-0.5"
                        >
                          <span className="min-w-0 flex-1">
                            <span className="block font-display font-bold" lang="en">
                              {alternative.name}
                            </span>
                            {alternative.agency && (
                              <span className="block text-sm text-ink-faint">
                                {alternative.agency}
                              </span>
                            )}
                          </span>
                          {alternative.fit !== null && (
                            <span className="numeric shrink-0 font-bold text-good-fg">
                              {alternative.fit}%
                            </span>
                          )}
                          <ArrowRight
                            className="h-4 w-4 shrink-0 text-accent-700"
                            aria-hidden="true"
                          />
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              )}

              <p className="flex items-start gap-2.5 text-sm text-ink-faint">
                <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                {t("disclaimer")}
              </p>
            </>
          )}
        </SheetBody>

        <SheetFooter>
          <Link
            href={`/schemes/${result.scheme_code}?tab=eligibility`}
            className="btn-secondary grow justify-center text-base"
          >
            {t("readTheRules")}
          </Link>
          <Link href="/onboarding" className="btn-primary grow justify-center text-base">
            {t("updateProfile")}
          </Link>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
