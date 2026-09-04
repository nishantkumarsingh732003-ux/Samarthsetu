"use client";

/**
 * The signed-in frame: a sidebar on a laptop, a bottom bar on a phone.
 *
 * Two navigations rather than a hamburger, because they are for different hands. The
 * bottom bar carries the five destinations a citizen actually returns to and sits inside
 * thumb reach; the sidebar carries everything and only exists where there is room for it.
 * A drawer that has to be opened before it can be read is a worse trade on the phone this
 * is built for.
 *
 * The account surface is deliberately *not* inside the < 200KB citizen-route budget that
 * `scripts/check-bundle.mjs` enforces. That budget protects the anonymous journey — the
 * path a first-time user on 2G walks with no login — which is still `/`, `/assist`,
 * `/results`, `/apply` and `/track`, and is untouched. Someone who has chosen to create
 * an account has already loaded that path once.
 */

import {
  Bot,
  Calculator,
  FileText,
  FolderOpen,
  LayoutDashboard,
  LogOut,
  MapPin,
  ScrollText,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { usePathname } from "next/navigation";

import { useAccount } from "@/components/account/AccountProvider";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Button } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";

import type { Locale } from "@/i18n/config";

interface Destination {
  href: string;
  labelKey: string;
  Icon: typeof LayoutDashboard;
}

const SIDEBAR: Destination[] = [
  { href: "/dashboard", labelKey: "dashboard", Icon: LayoutDashboard },
  { href: "/matches", labelKey: "matches", Icon: Sparkles },
  { href: "/schemes", labelKey: "schemes", Icon: ScrollText },
  { href: "/calculator", labelKey: "calculator", Icon: Calculator },
  { href: "/partners", labelKey: "partners", Icon: MapPin },
  { href: "/applications", labelKey: "applications", Icon: FileText },
  { href: "/documents", labelKey: "documents", Icon: FolderOpen },
  { href: "/assist", labelKey: "assist", Icon: Bot },
];

// The five a citizen comes back to. Thumb reach is scarce; this is what earns it.
const BOTTOM_BAR: Destination[] = [
  { href: "/dashboard", labelKey: "dashboard", Icon: LayoutDashboard },
  { href: "/matches", labelKey: "matches", Icon: Sparkles },
  { href: "/partners", labelKey: "partners", Icon: MapPin },
  { href: "/applications", labelKey: "applications", Icon: FileText },
  { href: "/profile", labelKey: "profile", Icon: UserRound },
];

export function AppShell({
  locale,
  children,
}: {
  locale: Locale;
  children: React.ReactNode;
}) {
  const t = useTranslations("nav");
  const { account, signOut } = useAccount();
  const pathname = usePathname();

  // `usePathname` from next-intl's navigation is already locale-stripped, but this
  // component uses next/navigation's, which is not — so compare on the suffix.
  const isCurrent = (href: string) =>
    pathname === `/${locale}${href}` || pathname.startsWith(`/${locale}${href}/`);

  return (
    <div className="flex min-h-screen">
      <a href="#main" className="skip-link">
        {t("skipToContent")}
      </a>

      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-line bg-surface lg:flex">
        <div className="px-5 py-5">
          <Brand />
        </div>

        <nav aria-label={t("primary")} className="flex-1 space-y-1 overflow-y-auto px-3">
          {SIDEBAR.map(({ href, labelKey, Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isCurrent(href) ? "page" : undefined}
              className={`flex min-h-touch items-center gap-3 rounded-card px-3 text-base
                          font-medium transition-colors ${
                            isCurrent(href)
                              ? "bg-accent-100 text-accent-800"
                              : "text-ink-muted hover:bg-accent-50 hover:text-accent-700"
                          }`}
            >
              <Icon className="h-5 w-5 shrink-0" aria-hidden="true" strokeWidth={2} />
              {t(labelKey)}
            </Link>
          ))}
        </nav>

        <div className="space-y-1 border-t border-line p-3">
          <Link
            href="/profile"
            className="flex min-h-touch items-center gap-3 rounded-card px-3 text-base
                       font-medium text-ink-muted hover:bg-accent-50 hover:text-accent-700"
          >
            <UserRound className="h-5 w-5" aria-hidden="true" />
            <span className="truncate">{account?.display_name ?? t("profile")}</span>
          </Link>
          <div className="px-3 py-1">
            <LanguageSwitcher locale={locale} />
          </div>
          <Button
            variant="quiet"
            onClick={signOut}
            className="w-full justify-start gap-3 px-3 hover:bg-stop-bg hover:text-stop-fg"
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
            {t("signOut")}
          </Button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex min-h-touch items-center justify-between gap-3 border-b border-line bg-surface px-4 lg:hidden">
          <Brand compact />
          <LanguageSwitcher locale={locale} />
        </header>

        <main id="main" className="ground-wash flex-1 px-4 pb-24 pt-6 lg:px-8 lg:pb-10">
          <div className="mx-auto max-w-6xl">{children}</div>
        </main>

        <nav
          aria-label={t("primary")}
          className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-surface lg:hidden"
        >
          {BOTTOM_BAR.map(({ href, labelKey, Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isCurrent(href) ? "page" : undefined}
              className={`flex min-h-touch flex-col items-center justify-center gap-0.5 py-1.5
                          text-xs ${
                            isCurrent(href) ? "text-accent-700" : "text-ink-faint"
                          }`}
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span className="truncate px-0.5">{t(labelKey)}</span>
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}

/** The mark. `सेतु` is the name in Devanagari — a bridge, which is what this is. */
function Brand({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("app");
  return (
    <span className="flex items-center gap-2.5">
      <span
        aria-hidden="true"
        className="grid h-9 w-9 shrink-0 place-items-center rounded-card bg-accent-700 font-display text-base font-bold text-white"
      >
        से
      </span>
      <span className="leading-tight">
        <span className="block font-display text-base font-bold">{t("title")}</span>
        {!compact && (
          <span className="block text-xs text-ink-faint">{t("ministryShort")}</span>
        )}
      </span>
    </span>
  );
}
