import { unstable_setRequestLocale } from "next-intl/server";

import { ApplicationsClient } from "@/app/[locale]/(account)/applications/ApplicationsClient";

import type { Locale } from "@/i18n/config";

export default function ApplicationsPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <ApplicationsClient locale={locale} />;
}
