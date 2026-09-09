import { unstable_setRequestLocale } from "next-intl/server";

import { ShortlistClient } from "@/app/[locale]/(account)/shortlist/ShortlistClient";

import type { Locale } from "@/i18n/config";

export default function ShortlistPage({
  params: { locale },
}: {
  params: { locale: Locale };
}) {
  unstable_setRequestLocale(locale);
  return <ShortlistClient locale={locale} />;
}
