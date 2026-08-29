import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import type { Locale } from "@/i18n/config";

import { ResultsClient } from "./ResultsClient";

export default async function Results({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <>
      <a href="#main" className="skip-link">
        {t("a11y.skipToContent")}
      </a>
      <main id="main" className="mx-auto max-w-md px-5 py-6">
        <Link href={`/${locale}/assist`} className="mb-4 inline-block text-base text-accent-700">
          ← {t("common.back")}
        </Link>
        <h1 className="mb-5 text-2xl font-semibold">{t("results.heading")}</h1>
        <ResultsClient locale={locale} />
      </main>
    </>
  );
}
