import {
  ArrowRight,
  BadgeCheck,
  Check,
  Languages,
  MapPin,
  ScrollText,
  Sparkles,
  UserRound,
} from "lucide-react";
import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import Link from "next/link";

import { FeaturedSchemes } from "@/components/landing/FeaturedSchemes";
import { MatchFlowPreview } from "@/components/landing/MatchFlowPreview";
import { SiteHeader } from "@/components/landing/SiteHeader";
import { StatStrip } from "@/components/landing/StatStrip";
import { StoryCarousel } from "@/components/landing/StoryCarousel";
import { schemeFact } from "@/lib/schemeFacts";
import { WORKED_EXAMPLE } from "@/lib/stories";

import type { Locale } from "@/i18n/config";

/**
 * The front door.
 *
 * Two things it must do and one it must not. It must make the primary action obvious —
 * signing in, which is where the eligibility check now begins — and it must be honest
 * that this is a hackathon prototype rather than a government portal. It must not sell.
 *
 * This is the only page a signed-out visitor sees. The anonymous journey that used to sit
 * behind it (`/assist` → `/results` → `/track`) has been removed: it duplicated the
 * signed-in surface screen for screen, and one journey that works is worth more than two
 * that drift apart. Partner routing and the application form kept their URLs but moved
 * into the `(account)` group, so they are gated rather than gone.
 *
 * Nearly all of it is a server component: the header, the hero, the worked example, the
 * four steps, the scheme cards and the footer are complete in the first HTML response,
 * so a citizen reads the page and can act on it before any JavaScript arrives. Only two
 * islands are interactive — the live counters and the story carousel — and both render
 * something meaningful before they hydrate.
 *
 * Every number on the page is either fetched from the API or computed from the versioned
 * rule pack. The design drop's "12,480+ entrepreneurs guided" and "92% match" are not
 * here, because on a page carrying a ministry's name an invented figure is a false claim
 * rather than placeholder copy — CLAUDE.md rule 6. See docs/DESIGN_PORT.md.
 */
export default async function Home({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();
  const app = t("app.title");

  const trust = [
    { Icon: BadgeCheck, label: t("landing.trustEligibility") },
    { Icon: Sparkles, label: t("landing.trustExplained") },
    { Icon: Languages, label: t("landing.trustLanguages") },
    { Icon: MapPin, label: t("landing.trustPartners") },
  ];

  const steps = [
    { n: "01", title: t("landing.step1Title"), body: t("landing.step1Body") },
    { n: "02", title: t("landing.step2Title"), body: t("landing.step2Body") },
    { n: "03", title: t("landing.step3Title"), body: t("landing.step3Body") },
    { n: "04", title: t("landing.step4Title"), body: t("landing.step4Body") },
  ];

  // The chips on the closing panel restate the worked example rather than inventing a
  // second citizen, so the page never shows two different "best matches".
  const example = schemeFact(WORKED_EXAMPLE.schemeCode);
  const readyChips = [
    t("landing.readyChipCategory"),
    t("landing.readyChipIncome"),
    t("landing.readyChipSector"),
    t("landing.readyChipLocation"),
  ];

  return (
    <div className="min-h-screen bg-surface">
      <SiteHeader locale={locale} />

      <main id="main">
        {/* --- hero ---------------------------------------------------------------- */}
        <section className="ground-wash bg-gradient-to-b from-canvas to-surface">
          <div className="mx-auto grid max-w-landing gap-8 px-5 py-10 lg:grid-cols-2 lg:items-center lg:gap-12 lg:px-8 lg:py-16">
            <div className="animate-rise">
              <p className="inline-flex items-center gap-2 rounded-full border border-line bg-surface px-4 py-1.5 text-sm font-medium text-ink-muted">
                <span aria-hidden="true" className="h-2 w-2 rounded-full bg-teal-600" />
                {t("landing.badge")}
              </p>

              <h1 className="mt-5 font-display text-3xl font-extrabold leading-[1.08] tracking-tight sm:text-4xl lg:text-[3.25rem] lg:leading-[1.05]">
                <span className="block">{t("landing.headlineA")}</span>
                <span className="block text-accent-600">{t("landing.headlineB")}</span>
                <span className="block text-teal-700">{t("landing.headlineC")}</span>
              </h1>

              <p className="mt-5 max-w-xl text-lg text-ink-muted">{t("landing.sub")}</p>

              {/* Sign-in first. The eligibility check, the matches and the partner
                  routing all live behind an account now — there is one journey, not two,
                  and this is its entrance. */}
              <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                <Link
                  href={`/${locale}/signin`}
                  className="btn rounded-full bg-accent-700 px-8 text-white hover:bg-accent-800"
                >
                  {t("landing.ctaCheck")}
                  <ArrowRight className="h-5 w-5" aria-hidden="true" />
                </Link>
                {/* An on-page anchor: the featured schemes are rendered further down and
                    are readable without an account, so sending someone to a login to see
                    what is already on the page they are reading is a dead end. */}
                <Link
                  href="#schemes"
                  className="btn rounded-full border-2 border-line bg-surface px-8 text-ink hover:border-accent-600"
                >
                  {t("landing.ctaSchemes")}
                </Link>
              </div>

              <ul className="mt-8 grid grid-cols-2 gap-x-6 gap-y-4 lg:grid-cols-4 lg:gap-x-4">
                {/* `min-w-0` + `hyphens-auto` on each row: a grid column will not shrink
                    below its longest unbreakable word, and "recommendations" is wider
                    than the 98px a 320px screen leaves beside the icon — it pushed the
                    whole landing page sideways. Hyphenation breaks it where the language
                    says to; `break-words` catches the scripts Chrome cannot hyphenate. */}
                {trust.map(({ Icon, label }) => (
                  <li key={label} className="flex min-w-0 items-start gap-2.5">
                    <Icon
                      className="mt-0.5 h-5 w-5 shrink-0 text-teal-700"
                      aria-hidden="true"
                    />
                    {/* `min-w-0` on the span as well as the row. `break-words` breaks a
                        long word once the box is already narrow, but it does not change
                        the box's *intrinsic* minimum — a flex item still refuses to go
                        below its longest word until this turns that minimum off. */}
                    <span className="hyphens-auto break-words min-w-0 font-medium">
                      {label}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <MatchFlowPreview locale={locale} />
          </div>
        </section>

        {/* --- what is in the system today ----------------------------------------- */}
        <section
          id="stats"
          className="scroll-mt-24 border-y border-line/70 bg-canvas"
          aria-labelledby="stats-heading"
        >
          <div className="mx-auto max-w-landing px-5 py-9 lg:px-8 lg:py-11">
            <h2 id="stats-heading" className="sr-only">
              {t("landing.statsTitle")}
            </h2>
            <StatStrip locale={locale} />
          </div>
        </section>

        {/* --- how it works --------------------------------------------------------- */}
        <section id="how" className="scroll-mt-24 bg-surface">
          <div className="mx-auto max-w-landing px-5 py-12 lg:px-8 lg:py-20">
            <p className="text-sm font-bold uppercase tracking-widest text-teal-700">
              {t("landing.howEyebrow")}
            </p>
            <h2 className="mt-2.5 font-display text-2xl font-extrabold tracking-tight lg:text-3xl">
              {t("landing.howTitle", { app })}
            </h2>
            <p className="mt-2.5 max-w-2xl text-ink-muted">{t("landing.howSub")}</p>

            <ol className="mt-8 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
              {steps.map((step) => (
                <li key={step.n} className="panel p-5">
                  <span className="numeric text-sm font-bold text-teal-700">{step.n}</span>
                  <h3 className="mt-3.5 font-display text-lg font-bold">{step.title}</h3>
                  <p className="mt-2 text-ink-muted">{step.body}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        {/* --- stories -------------------------------------------------------------- */}
        <section className="bg-surface" aria-labelledby="stories-heading">
          <div className="mx-auto max-w-landing px-5 pb-12 lg:px-8 lg:pb-20">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm font-bold uppercase tracking-widest text-teal-700">
                  {t("landing.storiesEyebrow")}
                </p>
                <h2
                  id="stories-heading"
                  className="mt-2.5 font-display text-2xl font-extrabold tracking-tight lg:text-3xl"
                >
                  {t("landing.storiesTitle")}
                </h2>
                <p className="mt-3 max-w-2xl text-lg text-ink-muted">
                  {t("landing.storiesSub")}
                </p>
              </div>
              {/* Not a decoration. Nobody in the carousel said the sentence attributed
                  to them, and the page has to say so where the quotes are. */}
              <p className="chip bg-saffron-bg text-saffron-fg">{t("landing.storiesBadge")}</p>
            </div>

            <div className="mt-10">
              <StoryCarousel locale={locale} />
            </div>
          </div>
        </section>

        {/* --- schemes -------------------------------------------------------------- */}
        <section id="schemes" className="scroll-mt-24 border-t border-line/70 bg-canvas">
          <div className="mx-auto max-w-landing px-5 py-12 lg:px-8 lg:py-20">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-sm font-bold uppercase tracking-widest text-teal-700">
                  {t("landing.schemesEyebrow")}
                </p>
                <h2 className="mt-2.5 font-display text-2xl font-extrabold tracking-tight lg:text-3xl">
                  {t("landing.schemesTitle")}
                </h2>
              </div>
              <Link
                href={`/${locale}/signin`}
                className="inline-flex items-center gap-2 font-medium text-accent-700 hover:text-accent-800"
              >
                {t("landing.schemesSeeAll")}
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>

            <div className="mt-10">
              <FeaturedSchemes locale={locale} />
            </div>

            {/* --- closing call to action ------------------------------------------ */}
            <div className="panel-dark mt-12 p-6 lg:p-10">
              <div className="grid gap-8 lg:grid-cols-[1.15fr_1fr] lg:items-center">
                <div>
                  <p className="text-sm font-bold uppercase tracking-widest text-saffron">
                    {t("landing.readyEyebrow")}
                  </p>
                  <h2 className="mt-2.5 font-display text-2xl font-extrabold tracking-tight lg:text-3xl">
                    {t("landing.readyTitle")}
                  </h2>
                  <p className="mt-3.5 max-w-lg text-white/80">{t("landing.readyBody")}</p>

                  {/* Stacked below `sm`, unlike the hero pair: this column is ~470px at
                      its widest and two buttons of Tamil or Telugu label do not fit side
                      by side in it — they get crushed to three wrapped lines each. */}
                  <div className="mt-7 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
                    <Link
                      href={`/${locale}/signin`}
                      className="btn rounded-full bg-white px-8 text-accent-700 hover:bg-accent-50"
                    >
                      {t("landing.ctaCheck")}
                      <ArrowRight className="h-5 w-5" aria-hidden="true" />
                    </Link>
                    <Link
                      href={`/${locale}/signin`}
                      className="btn rounded-full border-2 border-white/30 px-7 text-white hover:bg-white/10"
                    >
                      <UserRound className="h-5 w-5" aria-hidden="true" />
                      {t("landing.ctaSignIn")}
                    </Link>
                  </div>
                </div>

                <div>
                  <ul className="grid gap-3 sm:grid-cols-2">
                    {readyChips.map((chip) => (
                      <li
                        key={chip}
                        className="flex items-center gap-2.5 rounded-card border border-white/15 bg-white/10 px-4 py-3"
                      >
                        <Check className="h-5 w-5 shrink-0 text-good-bg" aria-hidden="true" />
                        <span className="min-w-0">{chip}</span>
                      </li>
                    ))}
                  </ul>

                  {example ? (
                    <div className="mt-3 rounded-card bg-surface p-4 text-ink">
                      <p className="text-sm font-medium uppercase tracking-wide text-ink-faint">
                        {t("landing.previewBestMatch")}
                      </p>
                      <p className="mt-1.5 flex flex-wrap items-baseline justify-between gap-3">
                        <span className="font-display text-base font-bold" lang="en">
                          {example.agency} {example.officialName}
                        </span>
                        <span className="numeric font-display text-xl font-extrabold text-teal-700">
                          {example.maxFundingPct}%
                        </span>
                      </p>
                      <p className="mt-1 text-sm text-ink-faint">
                        {t("landing.previewFunding", { pct: example.maxFundingPct })}
                      </p>
                    </div>
                  ) : null}
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-line bg-surface">
        <div className="mx-auto flex max-w-landing flex-wrap items-center justify-between gap-3 px-5 py-7 text-sm text-ink-faint lg:px-8">
          <p>{t("landing.copyright", { app })}</p>
          <p>{t("landing.notOfficial")}</p>
        </div>
      </footer>
    </div>
  );
}
