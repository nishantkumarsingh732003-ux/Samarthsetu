import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import type { Locale } from "@/i18n/config";

import { AssistClient } from "./AssistClient";

export default async function Assist({ params: { locale } }: { params: { locale: Locale } }) {
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
        <h1 className="mb-5 text-2xl font-semibold">{t("assist.heading")}</h1>
        <AssistClient locale={locale} />
      </main>
    </>
  );
}
