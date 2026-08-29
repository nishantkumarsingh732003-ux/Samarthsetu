import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";
import { Suspense } from "react";

import type { Locale } from "@/i18n/config";

import { PartnersClient } from "./PartnersClient";

export default async function Partners({
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
        <Link href={`/${locale}/results`} className="mb-4 inline-block text-base text-accent-700">
          ← {t("common.back")}
        </Link>
        <h1 className="mb-5 text-2xl font-semibold">{t("partners.heading")}</h1>
        <Suspense fallback={<p className="text-lg">{t("common.loading")}</p>}>
          <PartnersClient locale={locale} schemeCode={scheme} />
        </Suspense>
      </main>
    </>
  );
}
