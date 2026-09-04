"use client";

/**
 * Where a signed-in citizen lands.
 *
 * Four tiles and one card. The tiles answer "where do I stand"; the card answers "what
 * should I do next". Everything below that is a shortcut, not content — a dashboard that
 * needs scrolling to find the next step has failed at the only job it has.
 *
 * The "you could borrow" tile shows the engine's `indicative_amount` for the top scheme,
 * not a number computed here. Two ceilings apply to that figure — a percentage of project
 * cost and a cash cap — and recomputing it in the UI is how the two drift apart.
 */

import { Bot, Calculator, MapPin, Scale, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import { MatchCard } from "@/components/account/MatchCard";
import { schemeNamesFrom } from "@/components/account/schemeNames";
import { useMatches, useMyApplications } from "@/components/account/useCitizenData";
import { Button, ProgressBar } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { Locale } from "@/i18n/config";

export function DashboardClient({ locale }: { locale: Locale }) {
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");
  const { account, loadDemo } = useAccount();
  const matches = useMatches(locale);
  const applications = useMyApplications();
  const [loadingDemo, setLoadingDemo] = useState(false);

  const profile = account?.profile;
  const best = matches.data?.results.find((result) => result.rank === 1) ?? null;
  const usable = matches.data?.profile_is_usable ?? false;
  const firstName = (account?.display_name ?? "").split(" ")[0] || "";

  async function useSampleProfile() {
    setLoadingDemo(true);
    await loadDemo();
    matches.reload();
    setLoadingDemo(false);
  }

  const shortcuts = [
    {
      href: "/calculator",
      Icon: Calculator,
      title: t("planRepayment"),
      hint: t("planRepaymentHint"),
    },
    {
      href: "/partners",
      Icon: MapPin,
      title: t("findPartner"),
      hint: t("findPartnerHint"),
    },
    { href: "/compare", Icon: Scale, title: t("comparePlans"), hint: t("seeAll") },
    { href: "/assist", Icon: Bot, title: t("askAssistant"), hint: t("askAssistantHint") },
  ];

  return (
    <div className="space-y-8">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">
            {t("greeting", { name: firstName })}
          </h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
        </div>
        {profile && !profile.completed && (
          <Button variant="secondary" onClick={useSampleProfile} disabled={loadingDemo}>
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {loadingDemo ? t("demoLoading") : t("loadDemo")}
          </Button>
        )}
      </header>

      <section className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="panel p-4">
          <p className="text-sm text-ink-faint">{t("profileCompletion")}</p>
          <p className="numeric mt-1.5 font-display text-2xl font-extrabold text-accent-700">
            {profile?.completion_pct ?? 0}%
          </p>
          <div className="mt-2">
            <ProgressBar
              value={profile?.completion_pct ?? 0}
              label={t("profileCompletionHint", { answered: profile?.completion_pct ?? 0 })}
            />
          </div>
        </div>

        <div className="panel p-4">
          <p className="text-sm text-ink-faint">{t("bestMatch")}</p>
          <p className="mt-1.5 font-display text-lg font-bold text-teal-700">
            {best ? best.official_name : t("noMatchYet")}
          </p>
        </div>

        <div className="panel p-4">
          <p className="text-sm text-ink-faint">{t("funding")}</p>
          <p className="numeric mt-1.5 font-display text-2xl font-extrabold">
            {best?.indicative_amount != null
              ? formatRupees(best.indicative_amount, locale)
              : tCommon("notApplicable")}
          </p>
          {best && (
            <p className="mt-1 truncate text-sm text-ink-faint">
              {t("fundingHint", { scheme: best.official_name })}
            </p>
          )}
        </div>

        <div className="panel p-4">
          <p className="text-sm text-ink-faint">{t("applications")}</p>
          <p className="numeric mt-1.5 font-display text-2xl font-extrabold">
            {applications.data?.length ?? 0}
          </p>
          <p className="mt-1 truncate text-sm text-ink-faint">
            {applications.data?.[0]?.reference_no ?? t("noApplications")}
          </p>
        </div>
      </section>

      <section>
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-display text-xl font-bold">{t("bestMatchTitle")}</h2>
          <Link href="/matches" className="text-accent-700 underline">
            {t("seeAll")}
          </Link>
        </div>

        <div className="mt-4">
          {matches.loading && !matches.data ? (
            <p role="status" className="panel p-8 text-center text-ink-faint">
              {tCommon("loading")}
            </p>
          ) : best && usable ? (
            <MatchCard
              result={best}
              locale={locale}
              featured
              schemeNames={schemeNamesFrom(matches.data?.results)}
            />
          ) : (
            <div className="panel p-8 text-center">
              <h3 className="font-display text-lg font-bold">{t("emptyTitle")}</h3>
              <p className="mx-auto mt-2 max-w-md text-ink-muted">{t("emptyBody")}</p>
              <Link href="/onboarding" className="btn-primary mt-5">
                {t("startOnboarding")}
              </Link>
            </div>
          )}
        </div>
      </section>

      <section>
        <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {shortcuts.map(({ href, Icon, title, hint }) => (
            <li key={href}>
              <Link href={href} className="panel-link flex h-full items-start gap-3 p-4">
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-card bg-teal-50 text-teal-700">
                  <Icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <span>
                  <span className="block font-semibold">{title}</span>
                  <span className="mt-0.5 block text-sm text-ink-faint">{hint}</span>
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
