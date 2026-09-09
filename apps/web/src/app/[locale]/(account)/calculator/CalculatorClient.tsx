"use client";

/**
 * What the instalments look like, before anyone commits to anything.
 *
 * Pre-filled from the citizen's best match rather than from round numbers: the amount is
 * the engine's `indicative_amount`, the rate is the bottom of the scheme's published
 * band, and the tenure and moratorium are the scheme's own. A calculator that opens on
 * ₹9,00,000 at 8% for everybody is a toy; one that opens on *your* scheme's terms is the
 * screen that answers "can I afford this".
 *
 * The maths lives in `lib/emi.ts` and is unit-tested there, including the case the design
 * drop got wrong — a moratorium is a holiday from paying, not from interest.
 *
 * Export is `window.print()`, deliberately. The browser's own "Save as PDF" produces a
 * real PDF on a ₹6,000 Android phone with no library, no bytes and no server round trip;
 * a client-side PDF generator would cost ~300KB to do the same job worse. The print
 * stylesheet in globals.css drops the navigation so the sheet is the document.
 */

import { Download } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import { RepaymentPlanSheet } from "@/components/account/RepaymentPlanSheet";
import { useMatches } from "@/components/account/useCitizenData";
import { RepaymentChart } from "@/components/charts/RepaymentChart";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RangeField } from "@/components/ui/controls";
import { amortisationByYear, repaymentPlan } from "@/lib/emi";
import { formatRupees } from "@/lib/format";

import type { Locale } from "@/i18n/config";

const LIMITS = {
  amount: { min: 25000, max: 5000000, step: 5000 },
  rate: { min: 0, max: 14, step: 0.25 },
  years: { min: 1, max: 10, step: 1 },
  moratorium: { min: 0, max: 24, step: 1 },
};

export function CalculatorClient({ locale }: { locale: Locale }) {
  const t = useTranslations("calculator");
  const tCommon = useTranslations("common");
  const { data } = useMatches(locale);

  const [amount, setAmount] = useState(500000);
  const [rate, setRate] = useState(8);
  const [years, setYears] = useState(7);
  const [moratorium, setMoratorium] = useState(6);
  const [prefilledFrom, setPrefilledFrom] = useState<string | null>(null);

  // Adopt the best match's terms once they arrive, and only once — after that the
  // citizen owns the sliders and a late refetch must not yank them back.
  useEffect(() => {
    if (prefilledFrom || !data) return;
    const best = data.results.find(
      (result) => result.rank === 1 && result.indicative_amount !== null,
    );
    if (!best) return;

    setAmount(Math.round(best.indicative_amount!));
    if (best.indicative_interest_band) setRate(best.indicative_interest_band[0]);
    setPrefilledFrom(best.official_name);
  }, [data, prefilledFrom]);

  const plan = useMemo(
    () => repaymentPlan(amount, rate, years * 12, moratorium),
    [amount, rate, years, moratorium],
  );
  const schedule = useMemo(() => amortisationByYear(plan, rate), [plan, rate]);

  const money = (value: number) =>
    tCommon("rupees", { amount: formatRupees(value, locale) });

  /**
   * Stamped after mount, never during render. A `new Date()` in the render path makes the
   * server HTML and the first client HTML disagree, which is the exact class of bug
   * scripts/check-hydration.mjs fails the build for — and it is only wanted on the
   * printed sheet, which nobody sees before hydration anyway.
   */
  const [generatedAt, setGeneratedAt] = useState("");
  useEffect(() => {
    setGeneratedAt(
      new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date()),
    );
  }, [locale]);

  return (
    <div className="space-y-6">
      <header className="no-print">
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
        {prefilledFrom && (
          <p className="mt-1 text-sm text-teal-700">
            {t("prefill", { scheme: prefilledFrom })}
          </p>
        )}
      </header>

      <div className="no-print grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <Card>
          <CardContent className="space-y-6 p-5 lg:p-6">
          <RangeField
            label={t("amount")}
            numberLabel={t("amountBox")}
            value={amount}
            onChange={setAmount}
            display={money(amount)}
            {...LIMITS.amount}
          />
          <RangeField
            label={t("rate")}
            numberLabel={t("rateBox")}
            value={rate}
            onChange={setRate}
            display={t("ratePercent", { rate })}
            {...LIMITS.rate}
          />
          <RangeField
            label={t("years")}
            numberLabel={t("yearsBox")}
            value={years}
            onChange={setYears}
            display={t("yearsValue", { count: years })}
            {...LIMITS.years}
          />
          <div>
            <RangeField
              label={t("moratorium")}
              numberLabel={t("moratoriumBox")}
              value={moratorium}
              onChange={setMoratorium}
              display={t("monthsValue", { count: moratorium })}
              {...LIMITS.moratorium}
            />
            <p className="field-hint mt-2">{t("moratoriumHint")}</p>
          </div>
          </CardContent>
        </Card>

        <div className="space-y-5">
          <section className="panel-dark p-6 lg:p-7">
            <p className="text-xs font-bold uppercase tracking-widest text-saffron">
              {t("monthlyEmi")}
            </p>
            <p className="numeric mt-2 font-display text-4xl font-extrabold">
              {money(plan.emi)}
            </p>
            <dl className="mt-6 grid grid-cols-3 gap-3">
              {[
                { label: t("principal"), value: money(amount), tone: "" },
                {
                  label: t("totalInterest"),
                  value: money(plan.totalInterest),
                  // The one figure a borrower most needs to notice is what the credit
                  // costs on top of what they receive, so it is the one that is coloured.
                  tone: "text-saffron",
                },
                { label: t("totalPayment"), value: money(plan.totalPayment), tone: "" },
              ].map((stat) => (
                <div key={stat.label}>
                  <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-white/60">
                    {stat.label}
                  </dt>
                  <dd className={`numeric mt-1 font-semibold ${stat.tone}`}>
                    {stat.value}
                  </dd>
                </div>
              ))}
            </dl>
            {plan.moratoriumInterest > 0 && (
              <p className="numeric mt-4 border-t border-white/15 pt-3 text-sm text-white/75">
                {t("moratoriumInterest")}{" "}
                {money(plan.moratoriumInterest)}
              </p>
            )}
          </section>

          <Card>
            <CardContent className="p-5 lg:p-6">
              <h2 className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                {t("chartTitle")}
              </h2>
              <div className="mt-4">
                <RepaymentChart years={schedule} locale={locale} />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      <Card className="no-print">
        <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5 lg:p-6">
          <p className="max-w-2xl text-sm text-ink-faint">{t("disclaimer")}</p>
          {/* `window.print()` and not a PDF library — see RepaymentPlanSheet for why.
              The sheet below is what comes out. */}
          <Button
            variant="primary"
            onClick={() => window.print()}
            className="shrink-0 rounded-full"
          >
            <Download className="h-4 w-4" aria-hidden="true" />
            {t("download")}
          </Button>
        </CardContent>
      </Card>

      <RepaymentPlanSheet
        locale={locale}
        scheme={prefilledFrom}
        amount={amount}
        rate={rate}
        years={years}
        moratorium={moratorium}
        plan={plan}
        schedule={schedule}
        generatedAt={generatedAt}
      />
    </div>
  );
}
