import { unstable_setRequestLocale } from "next-intl/server";

import { CompareClient } from "@/app/[locale]/(account)/compare/CompareClient";

import type { Locale } from "@/i18n/config";

export default function ComparePage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <CompareClient locale={locale} />;
}
