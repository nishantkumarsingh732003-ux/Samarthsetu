import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import type { Locale } from "@/i18n/config";

export default async function Home({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-5 py-10">
      <header>
        <p className="text-sm font-medium uppercase tracking-widest text-ink-faint">
          {t("app.ministry")}
        </p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">{t("app.title")}</h1>
        <p className="mt-3 text-lg text-ink-muted">{t("app.tagline")}</p>
      </header>

      {/* One primary action. Nothing competes with it. */}
      <Link
        href={`/${locale}/assist`}
        aria-label={t("home.startAria")}
        className="btn-primary mt-10 w-full text-xl"
      >
        {t("home.start")}
      </Link>

      <Link href="/" className="mt-4 text-center text-base text-accent-700 underline">
        {t("common.changeLanguage")}
      </Link>
    </main>
  );
}
