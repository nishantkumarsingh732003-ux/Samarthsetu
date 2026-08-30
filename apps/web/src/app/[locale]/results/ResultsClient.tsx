"use client";

import { useTranslations } from "next-intl";
import Link from "next/link";
import { useEffect, useState } from "react";

import { SchemeCard } from "@/components/SchemeCard";
import { LOCALE_NAMES, isReviewed, type Locale } from "@/i18n/config";
import { loadResults, type SavedResults } from "@/lib/storage";

/**
 * Results are read from device storage rather than refetched.
 *
 * The citizen has just come from /assist, which wrote them. Reading locally means this
 * page works with the network gone — the offline requirement is satisfied by where the
 * data lives, not by a cache header.
 */
export function ResultsClient({ locale }: { locale: Locale }) {
  const t = useTranslations("results");
  const [saved, setSaved] = useState<SavedResults | null | undefined>(undefined);

  useEffect(() => {
    setSaved(loadResults());
  }, []);

  if (saved === undefined) return <p className="text-lg">…</p>;

  if (!saved || saved.results.length === 0) {
    return (
      <div className="card p-6 text-center">
        <p className="text-lg">{t("noResults")}</p>
        <Link href={`/${locale}/assist`} className="btn-primary mt-5 w-full">
          {t("empty")}
        </Link>
      </div>
    );
  }

  const explanations = new Map(saved.explanations.map((e) => [e.scheme_code, e]));
  const projectCost = Number(saved.profile.project_cost ?? 0) || null;
  const district = saved.district;
  const unreviewed = !isReviewed(locale);

  return (
    <div className="space-y-4">
      {unreviewed ? (
        <p className="rounded-card bg-warn-bg px-4 py-3 text-base text-warn-fg">
          {t("unreviewedTranslation", { language: LOCALE_NAMES[locale] })}
        </p>
      ) : null}

      {saved.results.map((result) => (
        <SchemeCard
          key={result.scheme_code}
          result={result}
          explanation={explanations.get(result.scheme_code)}
          locale={locale}
          projectCost={projectCost}
          district={district}
          matchRunId={saved.matchRunId ?? null}
        />
      ))}

      {/* The service matches and routes. A Channel Partner decides the loan. */}
      <p className="px-1 text-sm text-ink-faint">{t("indicativeOnly")}</p>
    </div>
  );
}
