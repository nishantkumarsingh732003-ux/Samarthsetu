import { unstable_setRequestLocale } from "next-intl/server";

import { SignInClient } from "@/app/[locale]/signin/SignInClient";

import type { Locale } from "@/i18n/config";

export default function SignInPage({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <SignInClient locale={locale} />;
}
