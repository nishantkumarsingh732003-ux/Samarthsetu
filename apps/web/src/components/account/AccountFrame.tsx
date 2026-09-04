"use client";

/**
 * The three states of a signed-in page, resolved once instead of in every page.
 *
 * `loading` renders the shell with a quiet placeholder rather than the sign-in prompt.
 * Treating "we are still checking the token" as "not signed in" flashes a login screen
 * at a returning citizen on every navigation, and on a 2G connection that is most
 * navigations.
 *
 * `anonymous` shows a prompt with two ways out — sign in, or check eligibility without
 * an account — rather than redirecting. A redirect loses where they were going and costs
 * another round trip to discover it.
 */

import { useTranslations } from "next-intl";
import Link from "next/link";

import { useAccount } from "@/components/account/AccountProvider";
import { AppShell } from "@/components/account/AppShell";

import type { Locale } from "@/i18n/config";

export function AccountFrame({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  const { status } = useAccount();
  const t = useTranslations("account");
  const tCommon = useTranslations("common");

  if (status === "loading") {
    return (
      <AppShell locale={locale}>
        <p role="status" className="py-16 text-center text-lg text-ink-faint">
          {tCommon("loading")}
        </p>
      </AppShell>
    );
  }

  if (status === "anonymous") {
    return (
      <div className="ground-wash flex min-h-screen items-center justify-center px-5 py-10">
        <div className="panel w-full max-w-md p-7">
          <h1 className="font-display text-2xl font-bold">{t("signInRequired")}</h1>
          <p className="mt-3 text-ink-muted">{t("signInPrompt")}</p>
          <div className="mt-6 flex flex-col gap-3">
            <Link href={`/${locale}/signin`} className="btn-primary">
              {t("goToSignIn")}
            </Link>
            <Link href={`/${locale}/assist`} className="btn-secondary">
              {t("checkAnonymously")}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return <AppShell locale={locale}>{children}</AppShell>;
}
