import { unstable_setRequestLocale } from "next-intl/server";

import { DocumentsClient } from "@/app/[locale]/(account)/documents/DocumentsClient";

import type { Locale } from "@/i18n/config";

export default function DocumentsPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <DocumentsClient locale={locale} />;
}
