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

import { Printer } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import { RepaymentChart } from "@/components/charts/RepaymentChart";
import { useMatches } from "@/components/account/useCitizenData";
import { Button, RangeField } from "@/components/ui/controls";
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

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
          {prefilledFrom && (
            <p className="mt-1 text-sm text-teal-700">
              {t("prefill", { scheme: prefilledFrom })}
            </p>
          )}
        </div>
        <Button variant="secondary" className="no-print" onClick={() => window.print()}>
          <Printer className="h-4 w-4" aria-hidden="true" />
          {t("print")}
        </Button>
      </header>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]">
        <section className="panel space-y-6 p-5">
          <RangeField
            label={t("amount")}
            numberLabel={t("amountBox")}
            value={amount}
            onChange={setAmount}
            display={formatRupees(amount, locale)}
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
        </section>

        <div className="space-y-5">
          <section className="panel-dark p-6">
            <p className="text-sm font-semibold uppercase tracking-wide text-saffron">
              {t("monthlyEmi")}
            </p>
            <p className="numeric mt-2 font-display text-4xl font-extrabold">
              {formatRupees(plan.emi, locale)}
            </p>
            <dl className="mt-5 grid grid-cols-3 gap-3">
              <div>
                <dt className="text-sm text-white/60">{t("principal")}</dt>
                <dd className="numeric mt-0.5 font-semibold">
                  {formatRupees(amount, locale)}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-white/60">{t("totalInterest")}</dt>
                <dd className="numeric mt-0.5 font-semibold">
                  {formatRupees(plan.totalInterest, locale)}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-white/60">{t("totalPayment")}</dt>
                <dd className="numeric mt-0.5 font-semibold">
                  {formatRupees(plan.totalPayment, locale)}
                </dd>
              </div>
            </dl>
            {plan.moratoriumInterest > 0 && (
              <p className="numeric mt-4 border-t border-white/15 pt-3 text-sm text-white/75">
                {t("moratoriumInterest")}{" "}
                {formatRupees(plan.moratoriumInterest, locale)}
              </p>
            )}
          </section>

          <section className="panel p-5">
            <h2 className="text-sm font-semibold text-ink-faint">{t("chartTitle")}</h2>
            <div className="mt-3">
              <RepaymentChart years={schedule} locale={locale} />
            </div>
          </section>
        </div>
      </div>

      <p className="text-sm text-ink-faint">{t("disclaimer")}</p>
    </div>
  );
}
