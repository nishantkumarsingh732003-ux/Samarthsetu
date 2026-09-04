import { unstable_setRequestLocale } from "next-intl/server";

import { DashboardClient } from "@/app/[locale]/(account)/dashboard/DashboardClient";

import type { Locale } from "@/i18n/config";

export default function DashboardPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <DashboardClient locale={locale} />;
}
