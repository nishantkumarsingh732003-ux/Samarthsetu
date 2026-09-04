"use client";

/**
 * Every scheme, in the order the engine put them, with the blocked ones still shown.
 *
 * Hiding the schemes a citizen does not qualify for would make a shorter page and a
 * worse one. "Why not that one?" is the question the whole project exists to answer —
 * an applicant who cannot see that the Micro Finance Scheme caps project cost at
 * ₹1,40,000 will keep asking about it at the branch counter.
 *
 * The engine stamp at the foot is not decoration. Engine version plus rules digest is
 * what makes a verdict reproducible: the same profile against the same pair gives the
 * same answer, and a changed digest is why an old answer no longer matches.
 */

import { useTranslations } from "next-intl";

import { MatchCard } from "@/components/account/MatchCard";
import { schemeNamesFrom } from "@/components/account/schemeNames";
import { useMatches } from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";

import type { Locale } from "@/i18n/config";

export function MatchesClient({ locale }: { locale: Locale }) {
  const t = useTranslations("matches");
  const tCommon = useTranslations("common");
  const { data, loading, error, reload } = useMatches(locale);

  const results = data?.results ?? [];
  const schemeNames = schemeNamesFrom(data?.results);
  const question = data?.next_question ?? null;

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      {error && (
        <p role="alert" className="rounded-card bg-warn-bg px-4 py-3 text-warn-fg">
          {error === "offline" ? tCommon("offline") : tCommon("error")}{" "}
          <Button variant="quiet" onClick={reload} className="ml-2 min-h-0 px-2 py-1">
            {tCommon("retry")}
          </Button>
        </p>
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
                schemeNames={schemeNames}
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
