import { unstable_setRequestLocale } from "next-intl/server";

import { CatalogueClient } from "@/app/[locale]/(account)/schemes/CatalogueClient";

import type { Locale } from "@/i18n/config";

export default function SchemesPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <CatalogueClient locale={locale} />;
}
