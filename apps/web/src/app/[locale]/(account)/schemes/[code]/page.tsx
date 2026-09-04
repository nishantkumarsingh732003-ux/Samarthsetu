import { unstable_setRequestLocale } from "next-intl/server";

import { SchemeDetailClient } from "@/app/[locale]/(account)/schemes/[code]/SchemeDetailClient";

import type { Locale } from "@/i18n/config";

export default function SchemeDetailPage({
  params: { locale, code },
}: {
  params: { locale: Locale; code: string };
}) {
  unstable_setRequestLocale(locale);
  return <SchemeDetailClient locale={locale} code={code} />;
}
