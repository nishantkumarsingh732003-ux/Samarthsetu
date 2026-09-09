"use client";

/**
 * Where a signed-in citizen lands.
 *
 * Four tiles, one card, three shortcuts. The tiles answer "where do I stand"; the card
 * answers "what should I do next". A dashboard that needs scrolling to find the next step
 * has failed at the only job it has.
 *
 * **Every figure comes from the engine, not from here.** The design drop filled this
 * screen with "NBCFDC Term Loan · for OBC entrepreneurs · ₹15,00,000 · 100% match".
 * None of that is in this system: the rule pack carries three NSFDC schemes, all
 * Scheduled Caste only, and what a given citizen can borrow is the run's
 * `indicative_amount` — a figure two ceilings apply to, a percentage of project cost and
 * a cash cap, which is exactly why it is read rather than recomputed in the UI.
 *
 * The interest band and tenure come from the published catalogue for whichever scheme
 * actually ranked first, so the card describes the scheme the engine chose rather than a
 * scheme chosen at design time.
 *
 * The layout is the drop's, down to the 2:1 split and the four tile tones. Two things in
 * it are not:
 *
 *   - **The application status is a translated label, not a prettified enum.** The drop
 *     showed "Under Review"; the code used to show `status.replace(/_/g, " ")`, which
 *     renders `PARTNER_ACKNOWLEDGED` as "partner acknowledged" and reads as a leaked
 *     internal. The `track.status` catalogue already had a sentence for every state in
 *     six languages, and this now uses it — the same words a citizen sees on the public
 *     tracking page for the same application.
 *   - **The completion tile tells the truth at 100%.** "Complete for better matches" is
 *     an instruction, and an instruction under a finished bar is noise. It is shown
 *     while there is something left to answer and swapped for a statement once there is
 *     not.
 */

import { ArrowRight, Bot, Calculator, MapPin, Sparkles } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import {
  useCatalogue,
  useMatches,
  useMyApplications,
} from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";
import { schemeFact } from "@/lib/schemeFacts";

import type { Locale } from "@/i18n/config";

/** Anything the tracking page has no sentence for is shown as the code rather than as a
 *  guess. A status this app does not know about is a deployment mismatch worth seeing. */
const TRACKED_STATUSES = new Set([
  "DRAFT",
  "SUBMITTED",
  "PARTNER_ACKNOWLEDGED",
  "DOCS_REQUESTED",
  "UNDER_APPRAISAL",
  "SANCTIONED",
  "DISBURSED",
  "REJECTED",
  "WITHDRAWN",
]);

export function DashboardClient({ locale }: { locale: Locale }) {
  const t = useTranslations("dashboard");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");
  const tTrack = useTranslations("track");
  const { account, loadDemo } = useAccount();
  const matches = useMatches(locale);
  const applications = useMyApplications();
  const catalogue = useCatalogue(locale);
  const [loadingDemo, setLoadingDemo] = useState(false);

  /**
   * Morning, afternoon or evening. Read in an effect and not during render: the server
   * has no idea what time it is where the citizen is, and reading the clock in the render
   * pass is the hydration mismatch `scripts/check-hydration.mjs` exists to catch.
   */
  const [partOfDay, setPartOfDay] = useState<
    "morning" | "afternoon" | "evening" | null
  >(null);
  useEffect(() => {
    const hour = new Date().getHours();
    setPartOfDay(hour < 12 ? "morning" : hour < 17 ? "afternoon" : "evening");
  }, []);

  const profile = account?.profile;
  const best =
    matches.data?.results.find((result) => result.rank === 1) ?? null;
  const usable = matches.data?.profile_is_usable ?? false;
  const firstName = (account?.display_name ?? "").split(" ")[0] || "";
  const application = applications.data?.[0] ?? null;
  const bestLimits =
    catalogue.data?.schemes.find((scheme) => scheme.code === best?.scheme_code)
      ?.limits ?? null;

  async function useSampleProfile() {
    setLoadingDemo(true);
    await loadDemo();
    matches.reload();
    setLoadingDemo(false);
  }

  const dash = tCommon("notApplicable");
  const money = (amount: number | null | undefined) =>
    amount == null
      ? dash
      : tCommon("rupees", { amount: formatRupees(amount, locale) });

  /** `fit.total` is the engine's own ranking score. `confidence` is a different thing —
   *  how sure the verdict is — and showing one under the other's label is how a number
   *  stops meaning anything. */
  const fitScore = best?.fit ? Math.round(best.fit.total) : null;

  const completion = profile?.completion_pct ?? 0;
  const statusCode = application?.status ?? null;

  const tiles = [
    {
      key: "completion",
      label: t("profileCompletion"),
      value: `${completion}%`,
      hint: completion >= 100 ? t("profileCompletionDone") : t("completionHint"),
      tone: "text-accent-700",
    },
    {
      key: "match",
      label: t("bestMatch"),
      value: fitScore == null ? dash : `${fitScore}%`,
      hint: best ? best.official_name : t("noMatchYet"),
      tone: "text-accent-700",
    },
    {
      key: "funding",
      label: t("funding"),
      value: money(profile?.loan_required ?? best?.indicative_amount),
      hint:
        profile?.project_cost != null
          ? t("fundingProject", { amount: money(profile.project_cost) })
          : best
            ? t("fundingHint", { scheme: best.official_name })
            : "",
      tone: "text-saffron-fg",
    },
    {
      key: "application",
      label: t("applicationStatus"),
      value: statusCode
        ? TRACKED_STATUSES.has(statusCode)
          ? tTrack(`status.${statusCode}`)
          : statusCode
        : t("noApplications"),
      hint: application?.reference_no ?? t("noApplicationsHint"),
      // A refusal is not good news and must not be printed in the colour of one.
      tone:
        statusCode === "REJECTED" || statusCode === "WITHDRAWN"
          ? "text-stop-fg"
          : "text-good-fg",
    },
  ];

  const shortcuts = [
    {
      // The in-shell chat, not the anonymous intake wizard at /assist.
      href: "/assistant",
      Icon: Bot,
      title: t("askAssistant"),
      hint: t("askAssistantHint"),
    },
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
      hint: profile?.district ?? t("findPartnerHint"),
    },
  ];

  return (
    <div className="space-y-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          {/* One step smaller on a phone. The root is 100% there and 80% on a desktop
              pointer (see globals.css), so `text-3xl` on a phone renders *larger* than
              `text-4xl` on a laptop — the greeting was breaking the emoji onto its own
              line at 390px while fitting comfortably at 1440. */}
          <h1 className="font-display text-2xl font-extrabold sm:text-3xl lg:text-4xl">
            {partOfDay
              ? t(`greeting.${partOfDay}`, { name: firstName })
              : t("greeting.neutral", { name: firstName })}{" "}
            <span aria-hidden="true">👋</span>
          </h1>
          <p className="mt-1.5 text-ink-muted">{t("sub")}</p>
        </div>
        {profile && !profile.completed && (
          <Button
            variant="secondary"
            onClick={useSampleProfile}
            disabled={loadingDemo}
          >
            <Sparkles className="h-4 w-4" aria-hidden="true" />
            {loadingDemo ? t("demoLoading") : t("loadDemo")}
          </Button>
        )}
      </header>

      <section className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {tiles.map((tile) => (
          <div key={tile.key} className="panel p-4 sm:p-5">
            <p className="text-xs font-bold uppercase leading-snug tracking-wider text-ink-faint sm:tracking-widest">
              {tile.label}
            </p>
            <p
              className={`numeric mt-2 font-display text-xl font-extrabold leading-tight
                          first-letter:uppercase sm:text-2xl lg:text-3xl ${tile.tone}`}
            >
              {tile.value}
            </p>
            {/* Two lines rather than an ellipsis. Half a tile is 123px on a 390px phone,
                and "Complete for better matches" truncated to "Nothing left to an…" is a
                sentence the citizen cannot finish — `title` does not exist on touch. */}
            <p className="mt-1.5 line-clamp-2 text-sm text-ink-faint" title={tile.hint}>
              {tile.hint}
            </p>
          </div>
        ))}
      </section>

      <section>
        <div className="flex items-center justify-between gap-3">
          <h2 className="font-display text-xl font-bold lg:text-2xl">
            {t("bestMatchTitle")}
          </h2>
          <Link
            href="/matches"
            className="inline-flex items-center gap-1.5 font-medium text-accent-700 hover:text-accent-800"
          >
            {t("seeAll")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </div>

        <div className="mt-3 grid gap-4 lg:grid-cols-[2fr_1fr] lg:items-start">
          <div>
            {matches.loading && !matches.data ? (
              <p role="status" className="panel p-8 text-center text-ink-faint">
                {tCommon("loading")}
              </p>
            ) : best && usable ? (
              <div className="panel-dark p-6 lg:p-8">
                <span className="chip bg-saffron-bg text-saffron-fg">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("bestMatchBadge")}
                </span>

                <h3
                  className="mt-4 font-display text-2xl font-extrabold lg:text-3xl"
                  lang="en"
                >
                  {best.official_name}
                </h3>
                <p className="mt-2 text-white/75">
                  {t("schemeSubtitle", {
                    agency: schemeFact(best.scheme_code)?.agency ?? "",
                    pct: best.max_funding_pct ?? 0,
                  })}
                </p>

                <dl className="mt-7 grid grid-cols-2 gap-x-4 gap-y-5 sm:grid-cols-4">
                  <div className="flex flex-col">
                    <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-white/60">
                      {t("statMatch")}
                    </dt>
                    <dd className="numeric mt-auto pt-1.5 font-display text-xl font-extrabold text-good-bg">
                      {fitScore == null ? dash : `${fitScore}%`}
                    </dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-white/60">
                      {t("statFinancing")}
                    </dt>
                    <dd className="numeric mt-auto pt-1.5 font-display text-xl font-extrabold">
                      {money(best.indicative_amount)}
                    </dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-white/60">
                      {t("statInterest")}
                    </dt>
                    <dd className="numeric mt-auto pt-1.5 font-display text-xl font-extrabold">
                      {best.indicative_interest_band
                        ? tMatches("perYearFlat", {
                            rate: best.indicative_interest_band[0],
                          })
                        : dash}
                    </dd>
                  </div>
                  <div className="flex flex-col">
                    <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-white/60">
                      {t("statTenure")}
                    </dt>
                    <dd className="numeric mt-auto pt-1.5 font-display text-xl font-extrabold">
                      {bestLimits?.tenure_months
                        ? t("tenureYears", {
                            years: Math.round(bestLimits.tenure_months / 12),
                          })
                        : dash}
                    </dd>
                  </div>
                </dl>

                <div className="mt-7 flex flex-col gap-3 sm:flex-row">
                  <Link
                    href={`/schemes/${best.scheme_code}`}
                    className="btn rounded-full bg-white px-6 text-accent-700 hover:bg-accent-50"
                  >
                    {t("viewScheme")}
                  </Link>
                  <Link
                    href="/compare"
                    className="btn rounded-full border-2 border-white/30 px-6 text-white hover:bg-white/10"
                  >
                    {t("comparePlans")}
                  </Link>
                </div>

                <p className="mt-4 text-sm text-white/60">{t("basedOnProfile")}</p>
              </div>
            ) : (
              <div className="panel p-8 text-center">
                <h3 className="font-display text-lg font-bold">
                  {t("emptyTitle")}
                </h3>
                <p className="mx-auto mt-2 max-w-md text-ink-muted">
                  {t("emptyBody")}
                </p>
                <Link href="/onboarding" className="btn-primary mt-5">
                  {t("startOnboarding")}
                </Link>
              </div>
            )}
          </div>

          <ul className="grid gap-4 sm:grid-cols-3 lg:grid-cols-1">
            {shortcuts.map(({ href, Icon, title, hint }) => (
              <li key={href}>
                <Link
                  href={href}
                  className="panel-link flex h-full items-start gap-3.5 p-5"
                >
                  <span className="grid h-11 w-11 shrink-0 place-items-center rounded-card bg-teal-50 text-teal-700">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <span className="min-w-0">
                    <span className="block font-display text-lg font-bold">
                      {title}
                    </span>
                    <span className="mt-0.5 block truncate text-sm text-ink-faint">
                      {hint}
                    </span>
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}
