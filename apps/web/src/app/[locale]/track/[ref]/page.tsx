import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import type { Locale } from "@/i18n/config";

/**
 * Application status timeline.
 *
 * Applications are created in Phase 5, so this renders the reference and the status
 * ladder a citizen will move along. It shows the shape of the journey rather than
 * pretending to have data it cannot yet have.
 */
const STAGES = [
  "SUBMITTED",
  "PARTNER_ACKNOWLEDGED",
  "DOCS_REQUESTED",
  "UNDER_APPRAISAL",
  "SANCTIONED",
  "DISBURSED",
] as const;

export default async function Track({
  params: { locale, ref },
}: {
  params: { locale: Locale; ref: string };
}) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <>
      <a href="#main" className="skip-link">
        {t("a11y.skipToContent")}
      </a>
      <main id="main" className="mx-auto max-w-md px-5 py-6">
        <Link href={`/${locale}`} className="mb-4 inline-block text-base text-accent-700">
          ← {t("common.back")}
        </Link>
        <h1 className="text-2xl font-semibold">{t("track.heading")}</h1>
        <p className="mt-2 text-base text-ink-muted">
          {t("track.reference")}:{" "}
          <code className="rounded bg-line/60 px-2 py-1 text-base">{ref}</code>
        </p>

        <ol className="mt-6 space-y-0">
          {STAGES.map((stage, index) => (
            <li key={stage} className="flex gap-4">
              <div className="flex flex-col items-center">
                <span
                  aria-hidden="true"
                  className="mt-1 h-4 w-4 shrink-0 rounded-full border-2 border-line bg-surface"
                />
                {index < STAGES.length - 1 ? (
                  <span aria-hidden="true" className="w-0.5 flex-1 bg-line" />
                ) : null}
              </div>
              <p className="pb-6 text-lg">{t(`track.status.${stage}` as "track.status.SUBMITTED")}</p>
            </li>
          ))}
        </ol>
      </main>
    </>
  );
}
