import { unstable_setRequestLocale } from "next-intl/server";

import { CoverageClient } from "@/app/[locale]/(account)/partners/CoverageClient";

import type { Locale } from "@/i18n/config";

export default function PartnersPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <CoverageClient locale={locale} />;
}
