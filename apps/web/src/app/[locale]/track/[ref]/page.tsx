import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";
import { Suspense } from "react";

import type { Locale } from "@/i18n/config";

import { TrackClient } from "./TrackClient";

/**
 * Application status and document upload.
 *
 * The reference number is the only key. There is no login: a citizen who has walked to
 * a cyber cafe with a number written on a slip of paper must be able to check their
 * application, and the response carries no personal data for that reason.
 */
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
        <Suspense fallback={<p className="text-lg">{t("common.loading")}</p>}>
          <TrackClient locale={locale} reference={decodeURIComponent(ref)} />
        </Suspense>
      </main>
    </>
  );
}
