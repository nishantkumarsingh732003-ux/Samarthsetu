import { unstable_setRequestLocale } from "next-intl/server";

import { CalculatorClient } from "@/app/[locale]/(account)/calculator/CalculatorClient";

import type { Locale } from "@/i18n/config";

export default function CalculatorPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <CalculatorClient locale={locale} />;
}
