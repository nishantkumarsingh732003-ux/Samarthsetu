import {
  BadgeCheck,
  Building2,
  Languages,
  MapPin,
  MessageSquareText,
  ScrollText,
} from "lucide-react";
import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import { LiveStats } from "@/components/account/LiveStats";

import type { Locale } from "@/i18n/config";

/**
 * The front door.
 *
 * Two things it must do and one it must not. It must make the primary action obvious —
 * checking eligibility, which needs no account — and it must be honest that this is a
 * hackathon prototype rather than a government portal. It must not sell.
 *
 * The numbers in the stats strip are fetched live from the API rather than written into
 * the page. The design drop had "12,480+ entrepreneurs guided" and "1,240 channel
 * partners" as literals; on a government-adjacent service those are not placeholder copy,
 * they are false claims. CLAUDE.md rule 6 says the demo path carries no mock data, and a
 * landing page is part of the demo path.
 *
 * A server component apart from the stats island, so a citizen on 2G gets the text and
 * the two buttons without waiting for any JavaScript at all.
 */
export default async function Home({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  const trust = [
    { Icon: ScrollText, label: t("landing.trustEligibility") },
    { Icon: BadgeCheck, label: t("landing.trustExplained") },
    { Icon: Languages, label: t("landing.trustLanguages") },
    { Icon: MapPin, label: t("landing.trustPartners") },
  ];

  const steps = [
    { n: "01", title: t("landing.step1Title"), body: t("landing.step1Body") },
    { n: "02", title: t("landing.step2Title"), body: t("landing.step2Body") },
    { n: "03", title: t("landing.step3Title"), body: t("landing.step3Body") },
    { n: "04", title: t("landing.step4Title"), body: t("landing.step4Body") },
  ];

  return (
    <div className="ground-wash min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-4">
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden="true"
            className="grid h-10 w-10 place-items-center rounded-card bg-accent-700 font-display text-lg font-bold text-white"
          >
            से
          </span>
          <span className="leading-tight">
            <span className="block font-display text-lg font-bold">{t("app.title")}</span>
            <span className="block text-xs text-ink-faint">{t("app.ministryShort")}</span>
          </span>
        </span>
        <Link href="/" className="btn-quiet text-sm">
          <Languages className="h-4 w-4" aria-hidden="true" />
          {t("common.changeLanguage")}
        </Link>
      </header>

      <main className="mx-auto max-w-6xl px-5 pb-16">
        <section className="animate-rise pt-6 lg:pt-12">
          <p className="text-sm font-medium uppercase tracking-widest text-teal-700">
            {t("landing.eyebrow")}
          </p>
          <h1 className="mt-3 max-w-3xl font-display text-3xl font-extrabold leading-tight lg:text-4xl">
            {t("landing.headline")}{" "}
            <span className="text-accent-700">{t("landing.headlineAccent")}</span>
          </h1>
          <p className="mt-4 max-w-2xl text-lg text-ink-muted">{t("landing.sub")}</p>

          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href={`/${locale}/assist`} className="btn-primary sm:min-w-64">
              {t("landing.ctaCheck")}
            </Link>
            <Link href={`/${locale}/signin`} className="btn-secondary">
              {t("landing.ctaSignIn")}
            </Link>
          </div>
          <p className="mt-3 text-sm text-ink-faint">{t("landing.noAccountNeeded")}</p>

          <ul className="mt-10 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {trust.map(({ Icon, label }) => (
              <li key={label} className="flex items-center gap-3">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-card bg-accent-50 text-accent-700">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span className="font-medium">{label}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="mt-14" aria-labelledby="stats-heading">
          <h2 id="stats-heading" className="sr-only">
            {t("landing.statsTitle")}
          </h2>
          <LiveStats locale={locale} />
        </section>

        <section className="mt-14" aria-labelledby="how-heading">
          <h2 id="how-heading" className="font-display text-2xl font-bold">
            {t("landing.howTitle")}
          </h2>
          <ol className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
            {steps.map((step) => (
              <li key={step.n} className="panel p-5">
                <span className="numeric text-sm font-bold text-teal-700">{step.n}</span>
                <h3 className="mt-3 font-display text-lg font-bold">{step.title}</h3>
                <p className="mt-1.5 text-ink-muted">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        <section className="panel-dark mt-14 p-8 lg:p-12">
          <div className="grid gap-8 lg:grid-cols-[1.4fr_1fr] lg:items-center">
            <div>
              <h2 className="font-display text-2xl font-extrabold lg:text-3xl">
                {t("landing.footerTitle")}
              </h2>
              <p className="mt-3 max-w-lg text-white/80">{t("landing.footerBody")}</p>
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <Link href={`/${locale}/assist`} className="btn-inverse">
                  {t("landing.ctaCheck")}
                </Link>
                <Link
                  href={`/${locale}/signin`}
                  className="btn border-2 border-white/30 text-white hover:bg-white/10"
                >
                  {t("landing.ctaSignIn")}
                </Link>
              </div>
            </div>
            <ul className="space-y-2.5">
              {[
                { Icon: MessageSquareText, label: t("nav.assist") },
                { Icon: Building2, label: t("nav.partners") },
                { Icon: ScrollText, label: t("nav.schemes") },
              ].map(({ Icon, label }) => (
                <li
                  key={label}
                  className="flex items-center gap-3 rounded-card border border-white/15 bg-white/10 px-4 py-3"
                >
                  <Icon className="h-5 w-5 shrink-0" aria-hidden="true" />
                  {label}
                </li>
              ))}
            </ul>
          </div>
        </section>
      </main>

      <footer className="border-t border-line py-6">
        <p className="mx-auto max-w-6xl px-5 text-sm text-ink-faint">
          {t("landing.notOfficial")}
        </p>
      </footer>
    </div>
  );
}
