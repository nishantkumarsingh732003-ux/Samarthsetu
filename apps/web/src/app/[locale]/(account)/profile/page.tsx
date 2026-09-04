import { unstable_setRequestLocale } from "next-intl/server";

import { ProfileClient } from "@/app/[locale]/(account)/profile/ProfileClient";

import type { Locale } from "@/i18n/config";

export default function ProfilePage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <ProfileClient locale={locale} />;
}
