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
 * The desktop top bar is now the one the design drop drew, in full: a search box, a
 * notification bell, judge mode, the language, and who is signed in. The first pass of
 * this shell left the search and the bell out on the grounds that neither had anything
 * behind it — a box that searches nothing and a bell that never rings are worse on a
 * ministry-branded page than the space they would fill. That reasoning was right about
 * the fakes and wrong about the conclusion: both now have real data behind them.
 *
 *   - `GlobalSearch` searches the published scheme catalogue and the partner directory,
 *     the two things a citizen looks for by name. Both endpoints already existed.
 *   - `NotificationBell` reads `GET /citizen/notifications` — the stored record of the
 *     messages this service actually sent, added for it. It composes nothing.
 *
 * Neither appears on the phone header, which has room for the brand and the language and
 * nothing else. Search is a destination there, not furniture.
 *
 * The account surface is deliberately *not* inside the < 200KB citizen-route budget that
 * `scripts/check-bundle.mjs` enforces. That budget protects the anonymous journey — the
 * path a first-time user on 2G walks with no login — which is still `/`, `/assist`,
 * `/results`, `/apply` and `/track`, and is untouched. Someone who has chosen to create
 * an account has already loaded that path once.
 */

import {
  Bookmark,
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
import { GlobalSearch } from "@/components/account/GlobalSearch";
import { NotificationBell } from "@/components/account/NotificationBell";
import { JudgeTourButton } from "@/components/JudgeTourButton";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/controls";
import { Separator } from "@/components/ui/separator";
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
  { href: "/shortlist", labelKey: "shortlist", Icon: Bookmark },
  { href: "/calculator", labelKey: "calculator", Icon: Calculator },
  { href: "/partners", labelKey: "partners", Icon: MapPin },
  { href: "/applications", labelKey: "applications", Icon: FileText },
  { href: "/documents", labelKey: "documents", Icon: FolderOpen },
  { href: "/assistant", labelKey: "assist", Icon: Bot },
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
  const tCommon = useTranslations("common");
  const { account, signOut } = useAccount();
  const pathname = usePathname();

  // `usePathname` from next-intl's navigation is already locale-stripped, but this
  // component uses next/navigation's, which is not — so compare on the suffix.
  const isCurrent = (href: string) =>
    pathname === `/${locale}${href}` ||
    pathname.startsWith(`/${locale}${href}/`);

  return (
    <div className="flex min-h-screen">
      <a href="#main" className="skip-link">
        {t("skipToContent")}
      </a>

      <aside className="no-print sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-line bg-surface lg:flex">
        <div className="px-4 py-4">
          <Brand />
        </div>

        <nav
          aria-label={t("primary")}
          className="flex-1 space-y-0.5 overflow-y-auto px-3"
        >
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
              <Icon
                className="h-5 w-5 shrink-0"
                aria-hidden="true"
                strokeWidth={2}
              />
              <span className="flex-1 truncate">{t(labelKey)}</span>
            </Link>
          ))}
        </nav>

        <Separator className="bg-line" />
        <div className="space-y-0.5 p-3">
          {/* The language row reads as a nav item with its value on the right, the way
              the design drew it — but the control is still the same accessible menu the
              rest of the app uses, so there is one implementation and not two. */}
          <span
            className="flex min-h-touch items-center justify-between gap-3 rounded-card
                       px-3 text-base font-medium text-ink-muted"
          >
            {tCommon("language")}
            <LanguageSwitcher locale={locale} className="border-0 px-1" />
          </span>
          <Link
            href="/profile"
            className="flex min-h-touch items-center gap-3 rounded-card px-3 text-base
                       font-medium text-ink-muted hover:bg-accent-50 hover:text-accent-700"
          >
            <UserRound className="h-5 w-5" aria-hidden="true" />
            <span className="truncate">{t("profile")}</span>
          </Link>
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
        <header className="no-print sticky top-0 z-20 flex min-h-touch items-center justify-between gap-3 border-b border-line bg-surface px-4 lg:hidden">
          <Brand compact />
          <LanguageSwitcher locale={locale} />
        </header>

        <header className="no-print sticky top-0 z-30 hidden items-center gap-3 border-b border-line bg-surface px-6 py-2.5 lg:flex">
          {/* Capped rather than elastic: a search box that grows to 900px on a wide
              monitor reads as the page's main content, which it is not. */}
          <GlobalSearch locale={locale} className="w-full max-w-xl" />

          <div className="ml-auto flex shrink-0 items-center gap-2">
            <NotificationBell locale={locale} />
            <JudgeTourButton />
            <LanguageSwitcher locale={locale} />
            <Link
              href="/profile"
              className="flex min-h-touch items-center gap-2.5 rounded-card px-2
                         transition-colors duration-200 ease-out hover:bg-accent-50"
            >
              <Avatar aria-hidden="true" className="h-9 w-9">
                <AvatarFallback className="bg-accent-700 font-display text-base font-bold text-white">
                  {(account?.display_name ?? "").trim().charAt(0) || "?"}
                </AvatarFallback>
              </Avatar>
              <span className="hidden max-w-[14rem] leading-tight xl:block">
                <span className="block truncate font-semibold">
                  {account?.display_name ?? t("profile")}
                </span>
                <span className="block truncate text-xs text-ink-faint">
                  {account?.email}
                </span>
              </span>
            </Link>
          </div>
        </header>

        <main
          id="main"
          className="ground-wash flex-1 px-4 pb-24 pt-6 lg:px-7 lg:pb-5 lg:pt-4"
        >
          <div className="mx-auto max-w-shell">{children}</div>
        </main>

        <nav
          aria-label={t("primary")}
          className="no-print fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-surface lg:hidden"
        >
          {BOTTOM_BAR.map(({ href, labelKey, Icon }) => (
            <Link
              key={href}
              href={href}
              aria-current={isCurrent(href) ? "page" : undefined}
              className={`flex min-h-touch flex-col items-center justify-center gap-0.5 py-1.5
                          text-xs ${
                            isCurrent(href)
                              ? "text-accent-700"
                              : "text-ink-faint"
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

/** The mark: the first letter of `समर्थ सेतु`, the name in Devanagari — a bridge, which
 *  is what this is. Matches components/landing/SiteHeader.tsx. */
function Brand({ compact = false }: { compact?: boolean }) {
  const t = useTranslations("app");
  return (
    <span className="flex items-center gap-2.5">
      <span className="relative shrink-0">
        <span
          aria-hidden="true"
          className="grid h-9 w-9 place-items-center rounded-card bg-accent-700 font-display text-base font-bold text-white"
        >
          स
        </span>
        {/* The saffron pip from the design drop. Decoration, and the one place saffron
            appears at this size — it is a fill here, never a text colour. */}
        <span
          aria-hidden="true"
          className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-saffron
                     ring-2 ring-surface"
        />
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
