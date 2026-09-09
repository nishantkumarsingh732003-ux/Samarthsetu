"use client";

/**
 * Every scheme, in the order the engine put them, with the blocked ones still shown.
 *
 * Hiding the schemes a citizen does not qualify for would make a shorter page and a
 * worse one. "Why not that one?" is the question the whole project exists to answer —
 * an applicant who cannot see that the Micro Finance Scheme caps project cost at
 * ₹1,40,000 will keep asking about it at the branch counter.
 *
 * The band at the top is the design drop's score hero. It reads off the *top-ranked
 * result the citizen can actually have* rather than off rank 1 unconditionally: when
 * every scheme is blocked, rank 1 is a blocked scheme, and a 90% ring above it would be
 * the most misleading thing on the page. In that case the band is not drawn and the
 * cards speak for themselves.
 *
 * Tenure and moratorium are on the published catalogue, not on a match result, so the
 * catalogue is fetched alongside and joined by scheme code. It is a public, unauthenticated,
 * server-cached endpoint, and the two requests go out together — the page does not wait
 * on one to start the other.
 *
 * The engine stamp at the foot is not decoration. Engine version plus rules digest is
 * what makes a verdict reproducible: the same profile against the same pair gives the
 * same answer, and a changed digest is why an old answer no longer matches.
 */

import { ArrowRight } from "lucide-react";
import { useTranslations } from "next-intl";

import { MatchCard } from "@/components/account/MatchCard";
import { ScoreRing } from "@/components/account/ScoreRing";
import { useCatalogue, useMatches } from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { schemeFact } from "@/lib/schemeFacts";

import type { Alternative } from "@/components/account/WhyNotSheet";
import type { Locale } from "@/i18n/config";

/** The word beside the ring. Thresholds, not a model — `fit.total` is a weighted score
 *  out of 100 and these are the three bands the design drop labelled. */
function bandKey(score: number): "bandHigh" | "bandGood" | "bandPartial" {
  if (score >= 80) return "bandHigh";
  if (score >= 50) return "bandGood";
  return "bandPartial";
}

export function MatchesClient({ locale }: { locale: Locale }) {
  const t = useTranslations("matches");
  const tCommon = useTranslations("common");
  const { data, loading, error, reload } = useMatches(locale);
  const catalogue = useCatalogue(locale);

  const results = data?.results ?? [];
  const question = data?.next_question ?? null;

  /**
   * What to offer someone a scheme turned away.
   *
   * The engine's own `redirect_suggestion` leads, because that is the rule pack itself
   * saying where this applicant belongs — `MF_PROJECT_COST_BAND` carries
   * `suggest_instead: NSFDC_TERM_LOAN`. Behind it come the other results in this run the
   * citizen actually qualifies for, in the order the engine ranked them. Nothing is
   * re-ranked here; this run is its own lookup table, which is also why no extra request
   * is needed to turn a scheme code into an official name (the bug OI-25 closed).
   */
  const alternativesFor = (result: (typeof results)[number]): Alternative[] => {
    const describe = (other: (typeof results)[number]): Alternative => ({
      code: other.scheme_code,
      name: other.official_name,
      agency: schemeFact(other.scheme_code)?.agency ?? null,
      fit: other.fit ? Math.round(other.fit.total) : null,
    });

    const suggested = result.redirect_suggestion
      ? results.find((other) => other.scheme_code === result.redirect_suggestion)
      : undefined;

    const rest = results.filter(
      (other) =>
        other.scheme_code !== result.scheme_code &&
        other.scheme_code !== suggested?.scheme_code &&
        other.verdict !== "INELIGIBLE",
    );

    return [...(suggested ? [suggested] : []), ...rest].map(describe);
  };

  const limitsFor = (code: string) =>
    catalogue.data?.schemes.find((scheme) => scheme.code === code)?.limits ?? null;

  // The best result that is not blocked. `results` is already in engine rank order and
  // verdict is the first key it sorts on, so this is a scan, not a re-sort.
  const attainable = results.find((result) => result.verdict !== "INELIGIBLE") ?? null;
  const heroScore = attainable?.fit ? Math.round(attainable.fit.total) : null;

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">
            {t("title")}
          </h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
        </div>
        {results.length > 1 && (
          <Link
            href="/compare"
            className="btn-quiet shrink-0 font-semibold text-accent-700"
          >
            {t("compareSchemes")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        )}
      </header>

      {error && (
        <p role="alert" className="rounded-card bg-warn-bg px-4 py-3 text-warn-fg">
          {error === "offline" ? tCommon("offline") : tCommon("error")}{" "}
          <Button variant="quiet" onClick={reload} className="ml-2 min-h-0 px-2 py-1">
            {tCommon("retry")}
          </Button>
        </p>
      )}

      {/* The score hero. The disclaimer under it is the whole reason the band is allowed
          to be this large: the number orders the list below, and it is not the verdict
          and not a prediction of what a Channel Partner will decide. */}
      {attainable && heroScore !== null && (
        <section className="panel-dark flex flex-wrap items-center gap-6 p-6 lg:gap-8 lg:p-8">
          <ScoreRing
            value={heroScore}
            label={t("profileMatchLabel", { pct: heroScore })}
            onDark
          />
          <div className="min-w-[16rem] flex-1">
            <p className="text-xs font-bold uppercase tracking-widest text-saffron">
              {t("profileMatchEyebrow")}
            </p>
            <h2 className="mt-1.5 font-display text-2xl font-extrabold lg:text-3xl">
              {t(bandKey(heroScore))}
            </h2>
            <p className="mt-2.5 max-w-2xl text-white/75">{t("profileMatchNote")}</p>
          </div>
        </section>
      )}

      {/* The single most useful next question, when the profile cannot decide yet. The
          engine chooses it by how many rules it would resolve, not by form order. */}
      {question && (
        <section className="panel border-accent-700/25 bg-accent-50 p-5">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-accent-800">
            {t("answerThis")}
          </h2>
          <p className="mt-2 text-lg font-medium">
            {question.question_i18n[locale] ?? question.question_i18n.en}
          </p>
          <Link href="/onboarding" className="btn-primary mt-4">
            {t("answerThis")}
          </Link>
        </section>
      )}

      {loading && !data ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : results.length === 0 ? (
        <p className="panel p-8 text-center text-ink-faint">{t("noResults")}</p>
      ) : (
        <ul className="space-y-4">
          {results.map((result) => (
            <li key={result.scheme_code}>
              <MatchCard
                result={result}
                locale={locale}
                featured={result.rank === 1}
                alternatives={alternativesFor(result)}
                limits={limitsFor(result.scheme_code)}
              />
            </li>
          ))}
        </ul>
      )}

      {data && (
        <p className="numeric text-sm text-ink-faint">
          {t("engineStamp", {
            version: data.engine_version,
            digest: data.rules_digest.slice(0, 12),
          })}
        </p>
      )}
    </div>
  );
}
