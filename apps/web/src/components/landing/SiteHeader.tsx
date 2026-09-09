import { getTranslations } from "next-intl/server";
import Link from "next/link";

import { JudgeTourButton } from "@/components/JudgeTourButton";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

import type { Locale } from "@/i18n/config";

/**
 * The landing page's own header.
 *
 * A server component with one client island in it — the language control — so a citizen
 * on 2G gets the brand, the navigation and the primary action as HTML, before any
 * JavaScript arrives. There is no hamburger: on a phone the two nav items that lead
 * somewhere off this page stay visible and the two that are on-page anchors are dropped,
 * because a menu that has to be opened before it can be read is worse than a shorter menu.
 *
 * Every item is an anchor into this page. The two that used to leave it — `Eligibility`
 * to the conversation and `Partners` to the coverage map — both landed somewhere a
 * visitor with no account could not read, so they now point at the sections that already
 * answer them: the four-step journey (step 02 is the eligibility check) and the counter
 * band (which carries the Channel Partner count). Nothing new was built for either.
 */
export async function SiteHeader({ locale }: { locale: Locale }) {
  const t = await getTranslations();

  const nav = [
    { href: "#how", label: t("landing.navHowItWorks") },
    { href: "#schemes", label: t("landing.navSchemes") },
    { href: "#how", label: t("landing.navEligibility") },
    { href: "#stats", label: t("landing.navPartners") },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-line/70 bg-canvas/85 backdrop-blur">
      <div className="mx-auto flex max-w-landing items-center gap-3 px-5 py-2.5 lg:gap-8 lg:px-8">
        <Link
          href={`/${locale}`}
          className="flex shrink-0 items-center gap-2.5 rounded-card"
        >
          <span aria-hidden="true" className="relative">
            <span className="grid h-10 w-10 place-items-center rounded-[0.8rem] bg-gradient-to-br from-teal-600 to-accent-700 font-display text-lg font-bold text-white">
              स
            </span>
            <span className="absolute -right-0.5 -top-0.5 h-2.5 w-2.5 rounded-full bg-saffron ring-2 ring-canvas" />
          </span>
          <span className="leading-tight">
            <span className="block font-display text-base font-bold tracking-tight">
              {t("app.title")}
            </span>
            <span className="block text-xs text-ink-faint">{t("app.ministryShort")}</span>
          </span>
        </Link>

        <nav aria-label={t("nav.primary")} className="flex items-center gap-1">
          {nav.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="hidden whitespace-nowrap rounded-card px-3 py-2 font-medium
                         text-ink-muted transition-colors hover:bg-accent-50
                         hover:text-accent-700 lg:inline-flex"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="ml-auto flex shrink-0 items-center gap-2 lg:gap-3">
          {/* `xl` rather than `2xl`: the walkthrough is the whole reason a judge opens
              this page, and at 1440 — the commonest laptop — the old breakpoint hid the
              one control they were looking for behind a nav bar with room to spare. */}
          <JudgeTourButton className="hidden xl:inline-flex" />

          <LanguageSwitcher locale={locale} />

          <Link
            href={`/${locale}/signin`}
            className="btn hidden rounded-full bg-accent-700 px-6 text-base text-white
                       hover:bg-accent-800 md:inline-flex"
          >
            {t("landing.ctaCheck")}
          </Link>
        </div>
      </div>
    </header>
  );
}
