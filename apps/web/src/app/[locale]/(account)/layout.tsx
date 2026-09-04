import { unstable_setRequestLocale } from "next-intl/server";

import { AccountProvider } from "@/components/account/AccountProvider";
import { AccountFrame } from "@/components/account/AccountFrame";

import type { Locale } from "@/i18n/config";

/**
 * The signed-in tree.
 *
 * A route group, so `(account)` never appears in a URL — these pages live at
 * `/en/dashboard`, `/en/matches` and so on, beside the anonymous journey rather than
 * under a prefix.
 *
 * The provider is mounted here and not in `[locale]/layout.tsx` on purpose: the
 * anonymous route is the one with the 200KB JavaScript budget, and it has no use for an
 * account context.
 */
export default function AccountLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: Locale };
}) {
  unstable_setRequestLocale(locale);
  return (
    <AccountProvider>
      <AccountFrame locale={locale}>{children}</AccountFrame>
    </AccountProvider>
  );
}
