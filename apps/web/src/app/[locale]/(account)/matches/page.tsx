import { unstable_setRequestLocale } from "next-intl/server";

import { MatchesClient } from "@/app/[locale]/(account)/matches/MatchesClient";

import type { Locale } from "@/i18n/config";

export default function MatchesPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <MatchesClient locale={locale} />;
}
