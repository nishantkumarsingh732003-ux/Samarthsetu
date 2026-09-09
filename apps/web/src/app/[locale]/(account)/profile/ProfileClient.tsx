"use client";

/**
 * What is stored, and — the part that matters — what the rules are allowed to read.
 *
 * The page is six cards of answers, each with its own Edit link back to the exact
 * onboarding step that owns those fields. That is the whole reason the sections are split
 * the way they are: "Edit" on a profile page that dumps you at question one of four is a
 * link a citizen uses once and then stops using. `/onboarding?step=3` lands on the money.
 *
 * TWO THINGS THIS PAGE WILL NOT SAY, both from the design drop.
 *
 *   1. The DBT card is not a checker. There is no NPCI mapper behind this product, so
 *      "One-tap DBT check" would be a button that invents a government record — and a
 *      citizen wrongly told their account is seeded finds out when a subsidy silently
 *      fails to arrive, months later. The card explains what seeding is, and the dialog
 *      behind it validates an IFSC on the device and hands them the official page.
 *      See components/account/DbtCheckDialog.tsx.
 *   2. The accessibility tiles are not decoration. They write a real preference that
 *      changes the whole interface. See components/account/DisplayPreferences.tsx.
 *
 * WHAT USED TO BE AT THE BOTTOM, and where it went. This page carried a panel printing
 * `profile.engine_profile` verbatim — the exact dictionary handed to the deterministic
 * engine — as the checkable form of CLAUDE.md rule 1. It was cut from the profile on
 * request. The guarantee is not: every match still names the rule ids that decided it
 * (`matched_because` / `blocked_because`), the eligibility sheet lists them criterion by
 * criterion, and the onboarding hint now points there rather than here. Sign out moved to
 * where it already was, in the sidebar.
 */

import { Landmark, Pencil, ShieldCheck } from "lucide-react";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import { DbtCheckDialog } from "@/components/account/DbtCheckDialog";
import { DisplayPreferences } from "@/components/account/DisplayPreferences";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { ProgressBar } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { Locale } from "@/i18n/config";

/** A card of answers, and the onboarding step that owns them. `step` is 1-based because
 *  it appears in a URL a citizen can see. */
interface Section {
  title: string;
  step: number;
  rows: [string, React.ReactNode][];
  /** A closing line under the rows, where the card has something to say about them. */
  note?: string;
}

export function ProfileClient({ locale }: { locale: Locale }) {
  const t = useTranslations("profilePage");
  const tOnboarding = useTranslations("onboarding");
  const { account } = useAccount();
  const [dbtOpen, setDbtOpen] = useState(false);

  const profile = account?.profile;
  if (!profile) return null;

  const dash = t("notAnswered");
  const text = (value: string | number | null) =>
    value === null || value === "" ? dash : String(value);
  const money = (value: number | null) => (value === null ? dash : formatRupees(value, locale));
  const bool = (value: boolean | null) =>
    value === null ? dash : value ? tOnboarding("yes") : tOnboarding("no");

  const sections: Section[] = [
    {
      title: t("sectionPersonal"),
      step: 1,
      rows: [
        [tOnboarding("fullName"), text(profile.display_name)],
        [tOnboarding("age"), text(profile.age)],
        [tOnboarding("gender"), text(profile.gender)],
        [tOnboarding("education"), text(profile.education_level)],
        [tOnboarding("occupation"), text(profile.occupation_type)],
      ],
    },
    {
      title: t("sectionSocial"),
      step: 1,
      rows: [
        [tOnboarding("category"), text(profile.category)],
        [tOnboarding("casteCertificate"), bool(profile.has_caste_certificate)],
        [tOnboarding("pwd"), bool(profile.is_pwd)],
        [tOnboarding("safai"), bool(profile.is_safai_karamchari)],
      ],
    },
    {
      title: t("sectionIncome"),
      step: 1,
      rows: [[tOnboarding("income"), money(profile.annual_family_income)]],
      // One row, and the row that decides the most. Saying so is worth more than the
      // whitespace it fills.
      note: t("incomeNote"),
    },
    {
      title: t("sectionEnterprise"),
      step: 2,
      rows: [
        [tOnboarding("sector"), text(profile.project_sector)],
        [tOnboarding("businessName"), text(profile.business_name)],
        [tOnboarding("businessStatus"), text(profile.business_status)],
        [tOnboarding("description"), text(profile.business_description)],
      ],
    },
    {
      title: t("sectionNeed"),
      step: 3,
      rows: [
        [tOnboarding("projectCost"), money(profile.project_cost)],
        [tOnboarding("ownContribution"), money(profile.own_contribution)],
        [tOnboarding("loanRequired"), money(profile.loan_required)],
      ],
    },
    {
      title: t("sectionLocation"),
      step: 4,
      rows: [
        [tOnboarding("state"), text(profile.state)],
        [tOnboarding("district"), text(profile.district)],
        [tOnboarding("city"), text(profile.city)],
        [tOnboarding("pincode"), text(profile.pincode)],
      ],
    },
  ];

  return (
    <div className="space-y-6">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
          <p className="mt-1 text-ink-muted">{t("sub")}</p>
          <p className="mt-1 text-sm text-ink-faint">{account?.email}</p>
        </div>

        {/* The completion figure, where the drop puts it — beside the title rather than
            in a band of its own. The bar is under it because a percentage on a page of
            percentages needs something to be a percentage *of*. */}
        <div className="w-full sm:w-64">
          <p className="text-xs font-semibold uppercase tracking-wider text-ink-faint">
            {t("completionLabel")}
          </p>
          <p className="numeric mt-0.5 font-display text-3xl font-extrabold text-accent-700">
            {profile.completion_pct}%
          </p>
          <div className="mt-2">
            <ProgressBar
              value={profile.completion_pct}
              label={t("completion", { pct: profile.completion_pct })}
            />
          </div>
        </div>
      </header>

      {/* Aadhaar-DBT. Explained, never asserted — see the file header. */}
      <Card interactive>
        <CardContent className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-prose">
            <p className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-teal-700">
              <Landmark className="h-4 w-4" aria-hidden="true" />
              {t("dbtEyebrow")}
            </p>
            <h2 className="mt-1.5 font-display text-lg font-bold">{t("dbtTitle")}</h2>
            <p className="mt-1 text-ink-muted">{t("dbtBody")}</p>
            <Badge tone="warn" className="mt-3">
              {t("dbtStatus")}
            </Badge>
          </div>
          <Button variant="secondary" onClick={() => setDbtOpen(true)}>
            <ShieldCheck className="h-4 w-4" aria-hidden="true" />
            {t("dbtOpen")}
          </Button>
        </CardContent>
      </Card>
      <DbtCheckDialog open={dbtOpen} onOpenChange={setDbtOpen} />

      <DisplayPreferences locale={locale} />

      <div className="grid gap-4 lg:grid-cols-2">
        {sections.map((section) => (
          <Card key={section.title} interactive>
            <CardContent>
              <div className="flex items-start justify-between gap-3">
                <h2 className="font-display text-lg font-bold">{section.title}</h2>
                {/* Straight to the step that owns these fields, not to question one. */}
                <Link
                  href={`/onboarding?step=${section.step}`}
                  className="btn-quiet -mr-2 -mt-2 shrink-0 text-sm"
                  aria-label={t("editSection", { section: section.title })}
                >
                  <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("edit")}
                </Link>
              </div>
              <dl className="mt-2">
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
              {section.note && (
                <p className="mt-3 rounded-card bg-accent-50 px-4 py-3 text-accent-800">
                  {section.note}
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

    </div>
  );
}
