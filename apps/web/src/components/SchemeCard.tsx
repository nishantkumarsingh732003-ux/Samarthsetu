"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useState } from "react";

import type { Locale } from "@/i18n/config";
import type { Explanation, MatchResult } from "@/lib/api";
import { formatRupees } from "@/lib/format";

import { ReadAloud } from "./ReadAloud";

/**
 * One scheme, eligible or not.
 *
 * An ineligible scheme is shown, greyed, with the exact blocking reason. Hiding it
 * would leave the citizen wondering whether we simply failed to consider it — and the
 * blocked card is where the redirect ("consider the Term Loan instead") lives, which is
 * the single most useful thing we can tell someone we have just refused.
 */
export function SchemeCard({
  result,
  explanation,
  locale,
  projectCost,
  district,
  matchRunId,
}: {
  result: MatchResult;
  explanation?: Explanation;
  locale: Locale;
  projectCost: number | null;
  district: string | null;
  matchRunId?: string | null;
}) {
  const t = useTranslations("results");
  const a11y = useTranslations("a11y");
  const [open, setOpen] = useState(false);
  const [fitOpen, setFitOpen] = useState(false);

  const blocked = result.verdict === "INELIGIBLE";
  const verdictLabel = {
    ELIGIBLE: t("eligible"),
    LIKELY_ELIGIBLE: t("likelyEligible"),
    INELIGIBLE: t("ineligible"),
    NEED_MORE_INFO: t("needMoreInfo"),
  }[result.verdict];

  const tone = blocked
    ? "border-line bg-canvas"
    : result.verdict === "LIKELY_ELIGIBLE"
      ? "border-warn-line bg-surface"
      : "border-good-line bg-surface";

  const reasons = blocked ? result.blocked_because : result.matched_because;

  return (
    <article
      className={`card border-2 p-5 ${tone} ${blocked ? "opacity-80" : ""}`}
      aria-label={a11y("schemeCard", { name: result.official_name, verdict: verdictLabel })}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          {/* The official name is a legal name: never translated, always Latin script. */}
          <h2 className="text-xl font-semibold">{result.official_name}</h2>
          <p
            className={`mt-1 text-base font-medium ${
              blocked ? "text-ink-muted" : "text-good-fg"
            }`}
          >
            {verdictLabel}
          </p>
        </div>
        {explanation ? (
          <ReadAloud text={`${result.official_name}. ${explanation.explanation}`} locale={locale} />
        ) : null}
      </div>

      {!blocked && result.indicative_amount !== null ? (
        <dl className="mt-4 grid grid-cols-2 gap-3 text-base">
          <div>
            <dt className="text-sm text-ink-faint">{t("amount")}</dt>
            <dd className="text-lg font-semibold">
              Rs {formatRupees(result.indicative_amount, locale)}
            </dd>
          </div>
          {result.indicative_interest_band ? (
            <div>
              <dt className="text-sm text-ink-faint">{t("interest")}</dt>
              <dd className="text-lg font-semibold">
                {result.indicative_interest_band[0]}–{result.indicative_interest_band[1]}%
              </dd>
            </div>
          ) : null}
          {result.max_funding_pct ? (
            <div className="col-span-2 text-sm text-ink-muted">
              {t("funding", { pct: result.max_funding_pct })}
            </div>
          ) : null}
        </dl>
      ) : null}

      {result.redirect_suggestion ? (
        <p className="mt-3 rounded-card bg-accent-50 px-3 py-2 text-base text-accent-800">
          {t("considerInstead", { scheme: result.redirect_suggestion })}
        </p>
      ) : null}

      {/* Why this scheme sits where it does. The engine decides the order; this
          explains it. A citizen who disagrees with a component can point at the one
          they disagree with, which a single opaque score never allows. */}
      {result.fit ? (
        <section className="mt-4" aria-labelledby={`fit-${result.scheme_code}`}>
          <button
            type="button"
            onClick={() => setFitOpen((value) => !value)}
            aria-expanded={fitOpen}
            className="flex w-full items-center justify-between gap-3 rounded-card border-2 border-line px-4 py-3 text-left"
          >
            <span id={`fit-${result.scheme_code}`} className="text-base">
              {t("fitHeading")}
            </span>
            <span className="shrink-0 text-lg font-semibold tabular-nums">
              {Math.round(result.fit.total)}
              <span className="text-sm font-normal text-ink-faint">/100</span>
            </span>
          </button>

          {fitOpen ? (
            <ul className="mt-3 space-y-3">
              {result.fit.components.map((component) => (
                <li key={component.key}>
                  <div className="flex items-baseline justify-between gap-3 text-base">
                    <span>{t(`fit.${component.key}` as "fit.purpose_fit")}</span>
                    <span className="shrink-0 tabular-nums text-ink-muted">
                      {Math.round(component.score)}
                      <span className="text-sm text-ink-faint">
                        {" "}
                        × {component.weight.toFixed(2)}
                      </span>
                    </span>
                  </div>
                  <div
                    role="meter"
                    aria-valuenow={Math.round(component.score)}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={t(`fit.${component.key}` as "fit.purpose_fit")}
                    className="mt-1 h-2 w-full rounded-full bg-line"
                  >
                    <div
                      className={`h-2 rounded-full ${
                        component.score >= 50 ? "bg-accent-600" : "bg-warn-line"
                      }`}
                      style={{ width: `${Math.round(component.score)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-sm text-ink-muted">{component.detail}</p>
                </li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="btn-secondary mt-3 w-full text-base"
      >
        {open ? t("hideWhy") : blocked ? t("whyNotThis") : t("whyThis")}
      </button>

      {open ? (
        <div className="mt-3 space-y-3 rounded-card bg-canvas p-4">
          {explanation ? <p className="text-base">{explanation.explanation}</p> : null}

          <ul className="space-y-2">
            {reasons.map((reason) => (
              <li key={reason.rule_id} className="text-base">
                <span aria-hidden="true">{blocked ? "✕ " : "✓ "}</span>
                {reason.message}
                {/* The rule id is the audit trail made visible: a citizen or an officer
                    can quote it and find the exact rule that decided this. */}
                <code className="ml-2 rounded bg-line/60 px-1.5 py-0.5 text-xs">
                  {reason.rule_id}
                </code>
              </li>
            ))}
          </ul>

          {result.warnings.length > 0 ? (
            <ul className="space-y-2 border-t border-line pt-3">
              {result.warnings.map((warning) => (
                <li key={warning.rule_id} className="text-base text-warn-fg">
                  <span aria-hidden="true">! </span>
                  {warning.message}
                  <code className="ml-2 rounded bg-line/60 px-1.5 py-0.5 text-xs">
                    {warning.rule_id}
                  </code>
                </li>
              ))}
            </ul>
          ) : null}

          <p className="border-t border-line pt-3 text-sm text-ink-faint">
            {t("ruleIds")}: {[...reasons, ...result.warnings].map((r) => r.rule_id).join(", ")}
          </p>
        </div>
      ) : null}

      {!blocked ? (
        <Link
          href={{
            pathname: `/${locale}/results/${result.scheme_code}/partners`,
            query: {
              ...(projectCost ? { amount: String(projectCost) } : {}),
              ...(district ? { district } : {}),
              // Carried so the application can name the family it belongs to and
              // the engine run that decided it, without a second round trip.
              family: result.family,
              ...(matchRunId ? { run: matchRunId } : {}),
            },
          }}
          className="btn-primary mt-4 w-full text-lg"
        >
          {t("findPartners")}
        </Link>
      ) : null}
    </article>
  );
}
