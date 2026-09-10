import { unstable_setRequestLocale } from "next-intl/server";

import { EkycClient } from "@/app/[locale]/(account)/ekyc/EkycClient";

import type { Locale } from "@/i18n/config";

/**
 * The liveness capture, reached from the profile.
 *
 * Not on the sidebar on purpose: it is a step inside identity, not a place a citizen
 * navigates to. The profile card is its only entrance, and that card carries the same
 * caveat this page does.
 */
export default function Ekyc({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <EkycClient locale={locale} />;
}
