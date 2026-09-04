import { unstable_setRequestLocale } from "next-intl/server";

import { OnboardingClient } from "@/app/[locale]/(account)/onboarding/OnboardingClient";

import type { Locale } from "@/i18n/config";

export default function OnboardingPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <OnboardingClient locale={locale} />;
}
