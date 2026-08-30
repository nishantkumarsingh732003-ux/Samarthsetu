import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";
import { Suspense } from "react";

import type { Locale } from "@/i18n/config";

import { ApplyClient } from "./ApplyClient";

export default async function Apply({
  params: { locale, scheme },
}: {
  params: { locale: Locale; scheme: string };
}) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <>
      <a href="#main" className="skip-link">
        {t("a11y.skipToContent")}
      </a>
      <main id="main" className="mx-auto max-w-md px-5 py-6">
        <Link
          href={`/${locale}/results/${scheme}/partners`}
          className="mb-4 inline-block text-base text-accent-700"
        >
          ← {t("common.back")}
        </Link>
        <h1 className="mb-1 text-2xl font-semibold">{t("apply.heading")}</h1>
        {/* Said before anything else on the page, because it is the single thing most
            often misunderstood about this scheme: SETU does not lend. */}
        <p className="mb-5 text-base text-ink-muted">{t("apply.notALoan")}</p>
        <Suspense fallback={<p className="text-lg">{t("common.loading")}</p>}>
          <ApplyClient locale={locale} schemeCode={scheme} />
        </Suspense>
      </main>
    </>
  );
}
