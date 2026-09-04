"use client";

/**
 * What is stored, and — the part that matters — what the rules are allowed to read.
 *
 * The "what the rule engine sees" panel prints `profile.engine_profile` verbatim: the
 * exact dictionary the API hands to the deterministic engine. It exists so the central
 * claim of this project stops being a claim. CLAUDE.md rule 1 says eligibility is never
 * decided by a language model and only the rule contract decides it; a citizen can check
 * that here by seeing that their business description, their business name and the amount
 * they said they needed are simply absent from the list.
 *
 * The consent note is not boilerplate either. A `consents` row was written before any of
 * this was stored — the database will not accept a citizen without one — and no
 * government ID is ever held in full.
 */

import { Pencil } from "lucide-react";
import { useTranslations } from "next-intl";

import { useAccount } from "@/components/account/AccountProvider";
import { Button, ProgressBar } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { CitizenProfile } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export function ProfileClient({ locale }: { locale: Locale }) {
  const t = useTranslations("profilePage");
  const tOnboarding = useTranslations("onboarding");
  const { account, signOut } = useAccount();

  const profile = account?.profile;
  if (!profile) return null;

  const dash = t("notAnswered");
  const text = (value: string | number | null) =>
    value === null || value === "" ? dash : String(value);
  const money = (value: number | null) => (value === null ? dash : formatRupees(value, locale));
  const bool = (value: boolean | null) =>
    value === null ? dash : value ? tOnboarding("yes") : tOnboarding("no");

  const sections: { title: string; rows: [string, React.ReactNode][] }[] = [
    {
      title: t("sectionPersonal"),
      rows: [
        [tOnboarding("fullName"), text(profile.display_name)],
        [tOnboarding("category"), text(profile.category)],
        [tOnboarding("age"), text(profile.age)],
        [tOnboarding("gender"), text(profile.gender)],
        [tOnboarding("income"), money(profile.annual_family_income)],
        [tOnboarding("education"), text(profile.education_level)],
        [tOnboarding("occupation"), text(profile.occupation_type)],
        [tOnboarding("casteCertificate"), bool(profile.has_caste_certificate)],
        [tOnboarding("pwd"), bool(profile.is_pwd)],
        [tOnboarding("safai"), bool(profile.is_safai_karamchari)],
      ],
    },
    {
      title: t("sectionEnterprise"),
      rows: [
        [tOnboarding("sector"), text(profile.project_sector)],
        [tOnboarding("businessName"), text(profile.business_name)],
        [tOnboarding("businessStatus"), text(profile.business_status)],
        [tOnboarding("description"), text(profile.business_description)],
      ],
    },
    {
      title: t("sectionMoney"),
      rows: [
        [tOnboarding("projectCost"), money(profile.project_cost)],
        [tOnboarding("ownContribution"), money(profile.own_contribution)],
        [tOnboarding("loanRequired"), money(profile.loan_required)],
      ],
    },
    {
      title: t("sectionLocation"),
      rows: [
        [tOnboarding("state"), text(profile.state)],
        [tOnboarding("district"), text(profile.district)],
        [tOnboarding("city"), text(profile.city)],
        [tOnboarding("pincode"), text(profile.pincode)],
      ],
    },
  ];

  const engineEntries = Object.entries(profile.engine_profile);

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
          <p className="mt-1 text-sm text-ink-faint">{account?.email}</p>
        </div>
        <Link href="/onboarding" className="btn-secondary text-base">
          <Pencil className="h-4 w-4" aria-hidden="true" />
          {t("edit")}
        </Link>
      </header>

      <section className="panel p-5">
        <p className="numeric font-display text-2xl font-extrabold text-accent-700">
          {profile.completion_pct}%
        </p>
        <p className="mt-1 text-ink-muted">
          {t("completion", { pct: profile.completion_pct })}
        </p>
        <div className="mt-3">
          <ProgressBar
            value={profile.completion_pct}
            label={t("completion", { pct: profile.completion_pct })}
          />
        </div>
      </section>

      {/* The claim, made checkable. */}
      <section className="panel border-accent-700/25 bg-accent-50 p-5">
        <h2 className="font-display text-lg font-bold text-accent-800">{t("engineTitle")}</h2>
        <p className="mt-2 text-accent-800">{t("engineBody")}</p>
        {engineEntries.length === 0 ? (
          <p className="mt-4 text-accent-800">{t("engineEmpty")}</p>
        ) : (
          <dl className="mt-4 grid gap-x-6 gap-y-2 sm:grid-cols-2">
            {engineEntries.map(([field, value]) => (
              <div key={field} className="flex justify-between gap-3 border-b border-accent-100 py-1.5">
                <dt className="numeric text-sm text-accent-800">{field}</dt>
                <dd className="numeric text-sm font-semibold text-accent-800">
                  {String(value)}
                </dd>
              </div>
            ))}
          </dl>
        )}
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        {sections.map((section) => (
          <section key={section.title} className="panel p-5">
            <h2 className="font-display text-lg font-bold">{section.title}</h2>
            <dl className="mt-3">
              {section.rows.map(([label, value]) => (
                <div
                  key={label}
                  className="flex justify-between gap-4 border-b border-line/70 py-2 last:border-0"
                >
                  <dt className="text-ink-muted">{label}</dt>
                  <dd className="numeric text-right font-medium">{value}</dd>
                </div>
              ))}
            </dl>
          </section>
        ))}
      </div>

      <section className="panel p-5">
        <h2 className="font-display text-lg font-bold">{t("consentTitle")}</h2>
        <p className="mt-2 text-ink-muted">{t("consentBody")}</p>
        <Button variant="secondary" onClick={signOut} className="mt-4">
          {t("signOut")}
        </Button>
      </section>
    </div>
  );
}
