"use client";

/**
 * "Why this scheme matches you" — the eligibility explanation, in a side panel.
 *
 * A panel rather than a centred modal because the explanation is read *against* the card
 * that opened it: a citizen comparing "₹15,00,000, 8%" on the card with "your project
 * cost ₹10,00,000, requirement up to ₹15,00,000" in the panel should be able to see both
 * at once. A modal covers the thing it is explaining.
 *
 * The scheme's rules are not on a match result — only the reasons are, and a reason
 * carries its id and its sentence but not the condition behind it. So the rule pack is
 * fetched when the panel opens, once, and cached for as long as this card is mounted.
 * Opening a panel is the moment a citizen has asked for the detail; loading it before
 * that would be three extra requests per screen for something most people never open.
 *
 * The stepper at the foot is the actual pipeline, not a decoration: the profile is read,
 * the deterministic rules run, financing is computed from the scheme's limits, the fit
 * score orders what survived, and the top of that order is what the card recommends.
 * CLAUDE.md rule 1 — no LLM anywhere in that chain — is the thing it is describing.
 */

import { Check, TrendingUp } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useCriteriaRows } from "@/components/account/useCriteriaRows";
import { ReadAloud } from "@/components/ReadAloud";
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

import type { MatchResult } from "@/lib/api";
import type { CitizenProfile, SchemeDetail } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

/** The five stages a result actually passes through. Labels only — the numbers are the
 *  order, and the order is the pipeline in `packages/rules`. */
const STEPS = ["stepProfile", "stepRules", "stepFinancing", "stepMatch", "stepRecommend"];

export function EligibilitySheet({
  open,
  onOpenChange,
  result,
  profile,
  locale,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  result: MatchResult;
  profile: CitizenProfile | null | undefined;
  locale: Locale;
}) {
  const t = useTranslations("eligibilitySheet");
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
  const fitScore = result.fit ? Math.round(result.fit.total) : null;

  // Read aloud gets the verdict and the reasons — the two things someone who cannot read
  // fluently came here for. Not the tables, which take a minute of speech to no purpose.
  const spoken = [
    result.official_name,
    ...result.matched_because.map((reason) => reason.message),
  ].join(" ");

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent closeLabel={tCommon("close")}>
        <SheetHeader>
          <p className="text-xs font-bold uppercase tracking-widest text-teal-700">
            {t("eyebrow")}
          </p>
          <SheetTitle className="mt-2">{t("title")}</SheetTitle>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-3">
            <SheetDescription>
              <span lang="en">{result.official_name}</span>
              {fitScore !== null && ` · ${t("profileMatch", { pct: fitScore })}`}
            </SheetDescription>
            {spoken && <ReadAloud text={spoken} locale={locale} variant="full" />}
          </div>
        </SheetHeader>

        <SheetBody className="space-y-3">
          {!scheme ? (
            <p role="status" className="py-8 text-center text-ink-faint">
              {tCommon("loading")}
            </p>
          ) : (
            <>
              {rows.map((row) => (
                <div
                  key={row.key}
                  title={row.ruleIds.join(", ")}
                  className={`rounded-card border p-4 ${
                    row.failed
                      ? "border-stop-line bg-stop-bg/40"
                      : row.passed
                        ? "border-good-line bg-good-bg/40"
                        : "border-line bg-canvas"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="flex items-center gap-2.5 font-semibold">
                      {row.passed && (
                        <Check
                          className="h-4 w-4 shrink-0 text-good-fg"
                          aria-hidden="true"
                        />
                      )}
                      {row.label}
                    </span>
                    <span
                      className={`text-xs font-bold uppercase tracking-widest ${
                        row.failed
                          ? "text-stop-fg"
                          : row.passed
                            ? "text-good-fg"
                            : "text-ink-faint"
                      }`}
                    >
                      {row.failed
                        ? t("notMet")
                        : row.passed
                          ? t("passed")
                          : t("notChecked")}
                    </span>
                  </div>

                  <dl className="mt-3 grid gap-3 sm:grid-cols-2">
                    <div>
                      <dt className="text-sm text-ink-faint">{t("yourProfile")}</dt>
                      <dd className="mt-0.5 font-semibold tabular-nums">{row.yours}</dd>
                    </div>
                    {row.required.length > 0 && (
                      <div>
                        <dt className="text-sm text-ink-faint">{t("requirement")}</dt>
                        <dd className="mt-0.5 font-semibold tabular-nums">
                          {row.required.join(" · ")}
                        </dd>
                      </div>
                    )}
                  </dl>
                </div>
              ))}

              <section className="rounded-card bg-accent-50 p-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-accent-800">
                  {t("whyRecommended")}
                </h3>
                <ol className="mt-4 flex justify-between gap-2">
                  {STEPS.map((step, index) => (
                    <li key={step} className="flex min-w-0 flex-1 flex-col items-center gap-1.5">
                      <span
                        aria-hidden="true"
                        className="numeric grid h-8 w-8 place-items-center rounded-full border border-accent-700/25 bg-surface text-sm font-bold text-accent-800"
                      >
                        {index + 1}
                      </span>
                      <span className="truncate text-center text-sm text-accent-800">
                        {t(step)}
                      </span>
                    </li>
                  ))}
                </ol>
              </section>

              {/* The disclaimer is the reason the panel is allowed to look this
                  confident. Nothing here predicts what a Channel Partner will decide. */}
              <p className="text-sm text-ink-faint">{t("disclaimer")}</p>
            </>
          )}
        </SheetBody>

        <SheetFooter>
          <Link
            href={`/schemes/${result.scheme_code}`}
            className="btn-primary grow justify-center text-base"
          >
            {t("openScheme")}
          </Link>
          <Link href="/calculator" className="btn-secondary grow justify-center text-base">
            <TrendingUp className="h-4 w-4" aria-hidden="true" />
            {t("calculateEmi")}
          </Link>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
}
