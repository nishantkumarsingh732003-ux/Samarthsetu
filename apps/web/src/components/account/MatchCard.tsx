"use client";

/**
 * One scheme result, drawn to the SamarthSetu design drop.
 *
 * The card the drop specifies: a chip row carrying the best-match flag, the lending
 * agency and the profile-match score; the scheme name; a four-figure strip of what the
 * money looks like; the criteria that passed as short scannable labels in two columns;
 * and the actions gathered into a fixed column on the right.
 *
 * Where the numbers come from, since none of them may be invented (CLAUDE.md rule 6):
 *
 *   potential financing  match result  `indicative_amount`
 *   interest             match result  `indicative_interest_band`
 *   tenure / moratorium  catalogue     `limits`, joined by the caller and passed in
 *   profile match        match result  `fit.total`, the engine ranking score
 *   agency               rule pack     `schemeFacts.ts`, which is pinned to the YAML
 *
 * A figure with no value behind it is not drawn rather than filled with a guess: the
 * Educational Loan Scheme states no tenure and no moratorium, so that card carries two
 * columns and not four.
 *
 * On explainability (CLAUDE.md rule 3). The drop shows short labels — "Family income
 * supported" — instead of the engine sentence, and puts the blocked reasons behind a
 * "Why not this scheme?" control. Nothing is discarded to achieve that:
 *
 *   - Each passed criterion carries the engine sentence and its rule id in `title`, so
 *     the full reasoning is one hover away and is in the DOM for anything reading it.
 *   - The blocked reasons open in place, in full, each with its rule id — the same text
 *     that used to sit expanded, now behind the control the drop draws for it.
 *
 * `MF_INCOME_CEILING` on this card is still the same id in the published rule pack at
 * /schemes and in the audit row behind the decision.
 */

import { Bookmark, BookmarkCheck, Check, Sparkles, TriangleAlert } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import { criterionKey } from "@/components/account/criteriaLabels";
import { EligibilitySheet } from "@/components/account/EligibilitySheet";
import { useShortlist } from "@/components/account/useShortlist";
import { WhyNotSheet, type Alternative } from "@/components/account/WhyNotSheet";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";
import { schemeFact } from "@/lib/schemeFacts";

import type { MatchResult } from "@/lib/api";
import type { SchemeLimits } from "@/lib/citizenApi";
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

/** Still used by /compare, /shortlist and the scheme detail page, which show the verdict
 *  word on its own without the rest of the card around it. */
export function VerdictChip({ verdict }: { verdict: MatchResult["verdict"] }) {
  const t = useTranslations("matches");
  return <Chip tone={VERDICT_TONE[verdict]}>{t(VERDICT_KEY[verdict])}</Chip>;
}

/** The score chip changes tone with the score, the way the drop colours it: green at the
 *  top, the house navy in the middle, amber once the profile stops fitting. */
function scoreTone(score: number): "good" | "accent" | "warn" {
  if (score >= 80) return "good";
  if (score >= 50) return "accent";
  return "warn";
}

export function MatchCard({
  result,
  locale,
  featured = false,
  alternatives = [],
  limits,
}: {
  result: MatchResult;
  locale: Locale;
  featured?: boolean;
  /** Other schemes in this run the citizen qualifies for, in engine rank order. Shown in
   *  the "why not" panel; the engine's own redirect leads them. */
  alternatives?: Alternative[];
  /** Tenure and moratorium, joined from the published catalogue by the caller. */
  limits?: SchemeLimits | null;
}) {
  const t = useTranslations("matches");
  const tShortlist = useTranslations("shortlist");
  const tCommon = useTranslations("common");
  const { has, toggle, ready, isFull } = useShortlist();
  const { account } = useAccount();
  const [showEligibility, setShowEligibility] = useState(false);
  const [showWhyNot, setShowWhyNot] = useState(false);

  const band = result.indicative_interest_band;
  const interest = band
    ? band[0] === band[1]
      ? t("perYearFlat", { rate: band[0] })
      : t("perYear", { min: band[0], max: band[1] })
    : null;

  const fitScore = result.fit ? Math.round(result.fit.total) : null;
  const agency = schemeFact(result.scheme_code)?.agency ?? null;
  const blocked = result.blocked_because.length > 0;

  const saved = has(result.scheme_code);
  const cannotSave = !saved && isFull;
  const saveLabel = saved
    ? tShortlist("remove")
    : cannotSave
      ? tShortlist("full")
      : tShortlist("save");

  /** Built rather than laid out, so a missing value closes its gap instead of printing an
   *  em dash. Funding share only fills a seat the catalogue join left empty. */
  const figures: { label: string; value: string }[] = [];
  if (result.indicative_amount !== null) {
    figures.push({
      label: t("potentialFinancing"),
      value: tCommon("rupees", {
        amount: formatRupees(result.indicative_amount, locale),
      }),
    });
  }
  if (interest) figures.push({ label: t("interest"), value: interest });
  if (limits?.tenure_months) {
    figures.push({
      label: t("tenure"),
      value: t("upToYears", { years: Math.round(limits.tenure_months / 12) }),
    });
  }
  if (limits?.moratorium_months) {
    figures.push({
      label: t("moratorium"),
      value: t("upToMonths", { count: limits.moratorium_months }),
    });
  }
  if (figures.length < 4 && result.max_funding_pct !== null) {
    figures.push({ label: t("fundingShare"), value: `${result.max_funding_pct}%` });
  }

  /**
   * The passed criteria as the drop lists them: one short label per criterion.
   *
   * Collapsing rule ids onto labels means several rules can land on the same row — a
   * Term Loan checks `TL_PROJECT_COST_FLOOR` and `TL_PROJECT_COST_CEILING`, and printing
   * "Project cost supported" twice reads as a rendering fault. They merge into one row,
   * and the `title` carries every sentence and every rule id that fed it, so merging
   * costs nothing that was traceable before.
   *
   * A rule the mapping has not been taught keys on its own id, so it stands as its own
   * row with the engine sentence — verbose rather than silently swallowed by a neighbour.
   */
  const criteria: { key: string; label: string; title: string }[] = [];
  for (const reason of result.matched_because) {
    const key = criterionKey(reason.rule_id);
    const detail = `${reason.message} (${reason.rule_id})`;
    const existing = key ? criteria.find((row) => row.key === key) : undefined;
    if (existing) {
      existing.title += `\n${detail}`;
    } else {
      criteria.push({
        key: key ?? reason.rule_id,
        label: key ? t(`criteria.${key}`) : reason.message,
        title: detail,
      });
    }
  }

  return (
    // Every card carries the same border, the best match included. The navy ring that
    // used to single it out was doing the "Best match" chip's job a second time, and it
    // made the top of the list read as a different component from the rest of it.
    //
    // What distinguishes a card now is the pointer: `interactive` brings `.lift`, which
    // paints the shadow once into a pseudo-element and animates only its opacity while
    // the card itself moves on `transform`. Both are compositor properties — animating
    // `box-shadow` directly would repaint a third of the viewport sixty times a second,
    // which is what scripts/measure-frames.mjs exists to prevent.
    <Card asChild interactive>
      <article className="grid gap-x-6 gap-y-5 p-5 lg:grid-cols-[minmax(0,1fr)_13.5rem] lg:p-6">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {featured && (
              <Chip tone="saffron" className="uppercase tracking-wide">
                <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                {t("bestMatch")}
              </Chip>
            )}
            {agency && <Chip tone="neutral">{agency}</Chip>}
            {fitScore !== null && (
              <Chip tone={scoreTone(fitScore)}>
                {t("profileMatchPct", { pct: fitScore })}
              </Chip>
            )}
          </div>

          {/* Official name verbatim, never machine-translated (CLAUDE.md). */}
          <h3
            className="mt-3 font-display text-xl font-extrabold tracking-tight"
            lang="en"
          >
            {result.official_name}
          </h3>

          {figures.length > 0 && (
            <dl className="mt-4 grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-4">
              {figures.map((figure) => (
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
          )}

          {criteria.length > 0 && (
            <ul className="mt-5 grid gap-x-8 gap-y-2.5 sm:grid-cols-2">
              {criteria.map((row) => (
                <li
                  key={row.key}
                  className="flex gap-2.5 text-ink-muted"
                  title={row.title}
                >
                  <Check
                    className="mt-1 h-4 w-4 shrink-0 text-good-fg"
                    aria-hidden="true"
                  />
                  <span>{row.label}</span>
                </li>
              ))}
            </ul>
          )}

          {blocked && (
            <p className="mt-5 flex items-start gap-2.5 rounded-card border border-saffron-line bg-saffron-bg px-4 py-3 text-saffron-fg">
              <TriangleAlert className="mt-1 h-4 w-4 shrink-0" aria-hidden="true" />
              {t("someCriteria")}
            </p>
          )}
        </div>

        {/* The action column. A wrapping row on a phone, where a stack of full-width
            buttons is a screen of scrolling for two links and a bookmark. */}
        <div className="flex flex-wrap items-center gap-2.5 lg:flex-col lg:items-stretch">
          <Button
            variant="secondary"
            size="icon"
            onClick={() => toggle(result.scheme_code)}
            disabled={!ready || cannotSave}
            aria-pressed={saved}
            aria-label={saveLabel}
            title={saveLabel}
            className={`order-last shrink-0 rounded-full lg:order-first lg:self-end ${
              saved ? "border-saffron text-saffron-fg" : ""
            }`}
          >
            {saved ? <BookmarkCheck aria-hidden="true" /> : <Bookmark aria-hidden="true" />}
          </Button>

          {/* Both explanations open beside the card rather than replacing it, so the
              figures being explained stay on screen. "View details" is the one link that
              leaves — it goes to the documents a citizen has to gather. */}
          <Button
            variant="primary"
            onClick={() => setShowEligibility(true)}
            className="grow justify-center text-base lg:grow-0"
          >
            {t("viewEligibility")}
          </Button>
          <Link
            href={`/schemes/${result.scheme_code}?tab=documents`}
            className="btn-secondary grow justify-center text-base lg:grow-0"
          >
            {t("details")}
          </Link>

          {blocked && (
            <button
              type="button"
              onClick={() => setShowWhyNot(true)}
              className="btn grow justify-center border-2 border-saffron-line bg-surface
                         text-base text-saffron-fg hover:bg-saffron-bg lg:grow-0"
            >
              {t("whyNotThis")}
            </button>
          )}
        </div>

        <EligibilitySheet
          open={showEligibility}
          onOpenChange={setShowEligibility}
          result={result}
          profile={account?.profile}
          locale={locale}
        />
        {blocked && (
          <WhyNotSheet
            open={showWhyNot}
            onOpenChange={setShowWhyNot}
            result={result}
            profile={account?.profile}
            alternatives={alternatives}
            locale={locale}
          />
        )}
      </article>
    </Card>
  );
}
