"use client";

/**
 * One scheme result, with the reasoning attached rather than hidden behind a link.
 *
 * The design drop led with a percentage — a "92% profile match" in a big ring. That
 * number is the *fit* score, which orders the list; it is not the verdict and it is not
 * a probability of approval. Leading with it invites both misreadings, so this leads
 * with the verdict word, puts the reasons directly under it, and files the fit score
 * under "why it ranks here" where it belongs.
 *
 * Every reason carries its rule id. That is the whole explainability claim made
 * checkable: `MF_INCOME_CEILING` on this card is the same id in the published rule pack
 * at /schemes, and in the audit row behind the decision.
 */

import { Check, ChevronRight, CircleAlert, Info, X } from "lucide-react";
import { useTranslations } from "next-intl";

import { ReadAloud } from "@/components/ReadAloud";
import { Chip } from "@/components/ui/controls";
import { Disclosure } from "@/components/ui/Panel";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { MatchResult, Reason } from "@/lib/api";
import type { Locale } from "@/i18n/config";

const VERDICT_TONE = {
  ELIGIBLE: "good",
  LIKELY_ELIGIBLE: "good",
  INELIGIBLE: "stop",
  NEED_MORE_INFO: "warn",
} as const;

const VERDICT_KEY = {
  ELIGIBLE: "eligible",
  LIKELY_ELIGIBLE: "likelyEligible",
  INELIGIBLE: "ineligible",
  NEED_MORE_INFO: "needMoreInfo",
} as const;

export function VerdictChip({ verdict }: { verdict: MatchResult["verdict"] }) {
  const t = useTranslations("matches");
  return <Chip tone={VERDICT_TONE[verdict]}>{t(VERDICT_KEY[verdict])}</Chip>;
}

function ReasonList({
  reasons,
  tone,
}: {
  reasons: Reason[];
  tone: "good" | "stop" | "warn";
}) {
  const Icon = tone === "good" ? Check : tone === "stop" ? X : CircleAlert;
  const colour =
    tone === "good" ? "text-good-fg" : tone === "stop" ? "text-stop-fg" : "text-warn-fg";
  return (
    <ul className="space-y-2">
      {reasons.map((reason) => (
        <li key={reason.rule_id} className="flex gap-2.5">
          <Icon className={`mt-1 h-4 w-4 shrink-0 ${colour}`} aria-hidden="true" />
          <span>
            {reason.message}{" "}
            <span className="numeric text-sm text-ink-faint">{reason.rule_id}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}

export function MatchCard({
  result,
  locale,
  featured = false,
  schemeNames,
}: {
  result: MatchResult;
  locale: Locale;
  featured?: boolean;
  /** code -> official name, so the redirect suggestion never shows a raw code. */
  schemeNames?: Record<string, string>;
}) {
  const t = useTranslations("matches");

  const band = result.indicative_interest_band;
  const interest = band
    ? band[0] === band[1]
      ? t("perYearFlat", { rate: band[0] })
      : t("perYear", { min: band[0], max: band[1] })
    : null;

  // Read aloud gets the reasons, not the whole card. Someone who cannot read fluently
  // needs the verdict and why — not the amounts, which they can see.
  const spoken = [
    ...result.matched_because.map((reason) => reason.message),
    ...result.blocked_because.map((reason) => reason.message),
  ].join(" ");

  return (
    <article className={`panel p-5 ${featured ? "ring-2 ring-accent-700" : ""}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <VerdictChip verdict={result.verdict} />
            {featured && <Chip tone="saffron">{t("bestMatch")}</Chip>}
            {/* The *scheme's* provenance is incomplete, not the citizen's answers. Saying
                "what is still missing" here reads as a fault of theirs. */}
            {result.needs_verification && (
              <Chip tone="warn">{t("unverifiedFigures")}</Chip>
            )}
          </div>
          {/* Official name verbatim, never machine-translated (CLAUDE.md). */}
          <h3 className="mt-2.5 font-display text-lg font-bold">{result.official_name}</h3>
        </div>
        {result.rank !== null && (
          <span className="numeric text-sm font-semibold text-ink-faint">
            {t("rank", { rank: result.rank })}
          </span>
        )}
      </div>

      {(result.indicative_amount !== null || interest) && (
        <dl className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {result.indicative_amount !== null && (
            <div>
              <dt className="text-sm text-ink-faint">{t("indicativeAmount")}</dt>
              <dd className="numeric mt-0.5 font-semibold">
                {formatRupees(result.indicative_amount, locale)}
              </dd>
            </div>
          )}
          {interest && (
            <div>
              <dt className="text-sm text-ink-faint">{t("interest")}</dt>
              <dd className="mt-0.5 font-semibold">{interest}</dd>
            </div>
          )}
          {result.max_funding_pct !== null && (
            <div>
              <dt className="text-sm text-ink-faint">{t("fundingShare")}</dt>
              <dd className="numeric mt-0.5 font-semibold">{result.max_funding_pct}%</dd>
            </div>
          )}
        </dl>
      )}

      {result.matched_because.length > 0 && (
        <section className="mt-4">
          <h4 className="text-sm font-semibold text-ink-faint">{t("whyMatched")}</h4>
          <div className="mt-2">
            <ReasonList reasons={result.matched_because} tone="good" />
          </div>
        </section>
      )}

      {result.blocked_because.length > 0 && (
        <section className="mt-4">
          <h4 className="text-sm font-semibold text-ink-faint">{t("whyBlocked")}</h4>
          <div className="mt-2">
            <ReasonList reasons={result.blocked_because} tone="stop" />
          </div>
        </section>
      )}

      {result.warnings.length > 0 && (
        <section className="mt-4">
          <ReasonList reasons={result.warnings} tone="warn" />
        </section>
      )}

      {/* The engine returns an internal code here — NSFDC_TERM_LOAN — and printing it
          raw is exactly the bug OI-25 closed on the explanation path, reappearing through
          a different door. Resolved against the other results, which carry the official
          names, and falling back to the code only if it names a scheme not in this run. */}
      {result.redirect_suggestion && (
        <p className="mt-4 flex items-start gap-2 rounded-card bg-accent-50 px-3 py-2.5 text-accent-800">
          <Info className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
          {t("tryInstead", {
            scheme:
              schemeNames?.[result.redirect_suggestion] ?? result.redirect_suggestion,
          })}
        </p>
      )}

      {result.fit && result.fit.components.length > 0 && (
        <Disclosure summary={t("whyRanked")} className="mt-4">
          <ul className="space-y-1.5">
            {result.fit.components.map((component) => (
              <li key={component.key} className="flex justify-between gap-4">
                <span className="text-ink-muted">{component.detail}</span>
                <span className="numeric shrink-0 text-sm text-ink-faint">
                  {component.contribution.toFixed(1)}
                </span>
              </li>
            ))}
          </ul>
        </Disclosure>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <Link href={`/schemes/${result.scheme_code}`} className="btn-secondary text-base">
          {t("seeDetail")}
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Link>
        {result.verdict !== "INELIGIBLE" && (
          <Link
            href={`/results/${result.scheme_code}/partners`}
            className="btn-primary text-base"
          >
            {t("findPartners")}
          </Link>
        )}
        {spoken && <ReadAloud text={spoken} locale={locale} />}
      </div>
    </article>
  );
}
