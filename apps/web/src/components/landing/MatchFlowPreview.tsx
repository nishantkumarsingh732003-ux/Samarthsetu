import { Sparkles } from "lucide-react";
import { getTranslations } from "next-intl/server";

import { formatRupees } from "@/lib/format";
import { repaymentPlan } from "@/lib/emi";
import {
  SCHEME_FACTS,
  TERM_LOAN_REPAYMENT,
  lastVerifiedOn,
  schemeFact,
} from "@/lib/schemeFacts";
import { WORKED_EXAMPLE, WORKED_EXAMPLE_INCOME } from "@/lib/stories";

import type { Locale } from "@/i18n/config";

/**
 * The card beside the headline: one citizen's route through the system, end to end.
 *
 * Every figure on it is computed here, on the server, from the rule pack and the seeded
 * persona — the scheme names come from `schemeFacts.ts`, the instalment from the same
 * `repaymentPlan()` the calculator screen uses, and the profile from the persona
 * `scripts/seed/demo.py` actually creates. Nothing is typed in, and nothing is fetched,
 * so the card is complete in the first HTML response with no JavaScript and no spinner.
 *
 * It is labelled a worked example rather than a live feed, because that is what it is.
 * The design drop had this pulsing "Realtime" with a 92% match on a scheme this rule
 * pack does not carry; a number that looks live and is not is the one thing a page
 * carrying a ministry's name cannot do.
 */
export async function MatchFlowPreview({ locale }: { locale: Locale }) {
  const t = await getTranslations();
  const money = (amount: number) =>
    t("common.rupees", { amount: formatRupees(amount, locale) });

  const termLoan = schemeFact(WORKED_EXAMPLE.schemeCode);
  const microFinance = schemeFact("NSFDC_MICRO_FINANCE");
  if (!termLoan || !microFinance) return null;

  const plan = repaymentPlan(
    WORKED_EXAMPLE.amount,
    termLoan.interestRate,
    TERM_LOAN_REPAYMENT.tenureMonths,
    TERM_LOAN_REPAYMENT.moratoriumMonths,
  );

  const steps = [
    {
      n: "01",
      tone: "bg-accent-50 text-accent-800",
      label: t("landing.previewStep1"),
      detail: t("landing.previewStep1Detail", {
        name: WORKED_EXAMPLE.name.split(" ")[0],
        income: money(WORKED_EXAMPLE_INCOME),
      }),
    },
    {
      n: "02",
      tone: "bg-accent-50 text-accent-800",
      label: t("landing.previewStep2"),
      detail: t("landing.previewStep2Detail", { count: SCHEME_FACTS.length }),
    },
    {
      n: "03",
      tone: "bg-good-bg text-good-fg",
      label: t("landing.previewStep3"),
      // Verbatim scheme names on both sides: this line is the whole product in one
      // sentence — he asked for the small one and the engine named the one that fits.
      detail: t("landing.previewStep3Detail", {
        scheme: termLoan.officialName,
        other: microFinance.officialName,
      }),
    },
    {
      n: "04",
      tone: "bg-saffron-bg text-saffron-fg",
      label: t("landing.previewStep4"),
      detail: t("landing.previewStep4Detail", {
        emi: money(plan.emi),
        years: Math.round(TERM_LOAN_REPAYMENT.tenureMonths / 12),
      }),
    },
    {
      n: "05",
      tone: "bg-teal-50 text-teal-700",
      label: t("landing.previewStep5"),
      detail: t("landing.previewStep5Detail", { district: WORKED_EXAMPLE.district }),
    },
  ];

  return (
    <div className="panel p-4 sm:p-6">
      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="grid h-9 w-9 shrink-0 place-items-center rounded-card bg-accent-50 text-accent-700"
        >
          <Sparkles className="h-5 w-5" />
        </span>
        <div className="min-w-0">
          <p className="text-sm text-ink-faint">{t("landing.previewKicker")}</p>
          <h2 className="font-display text-lg font-bold">{t("landing.previewTitle")}</h2>
        </div>
        <span className="chip ml-auto shrink-0 bg-good-bg text-good-fg">
          <span aria-hidden="true" className="h-2 w-2 rounded-full bg-good-fg" />
          {t("landing.previewVerified", { date: lastVerifiedOn() })}
        </span>
      </div>

      <ol className="mt-4 space-y-2">
        {steps.map((step) => (
          <li key={step.n} className="flex items-center gap-3">
            <span
              aria-hidden="true"
              className={`numeric grid h-8 w-8 shrink-0 place-items-center rounded-card
                          text-sm font-bold ${step.tone}`}
            >
              {step.n}
            </span>
            <span
              className="flex min-w-0 flex-1 flex-wrap items-baseline justify-between gap-x-3
                         gap-y-0.5 rounded-card border border-line px-3.5 py-2"
            >
              <span className="font-semibold">{step.label}</span>
              <span className="text-sm text-ink-faint">{step.detail}</span>
            </span>
          </li>
        ))}
      </ol>

      <div className="panel-dark mt-4 p-4">
        <p className="flex flex-wrap items-baseline justify-between gap-2 text-sm text-white/70">
          {t("landing.previewBestMatch")}
          <span>{t("landing.previewFunding", { pct: termLoan.maxFundingPct })}</span>
        </p>
        <p className="mt-1.5 flex flex-wrap items-baseline justify-between gap-3">
          <span className="font-display text-lg font-bold">
            {termLoan.agency} {termLoan.officialName}
          </span>
          <span className="numeric font-display text-2xl font-extrabold text-good-bg">
            {termLoan.maxFundingPct}%
          </span>
        </p>
        <span
          aria-hidden="true"
          className="mt-3 block h-2 w-full overflow-hidden rounded-full bg-white/15"
        >
          <span
            className="block h-full rounded-full bg-good-bg"
            style={{ width: `${termLoan.maxFundingPct}%` }}
          />
        </span>
        <p className="mt-3 text-sm text-white/70">{t("landing.previewFooting")}</p>
      </div>
    </div>
  );
}
