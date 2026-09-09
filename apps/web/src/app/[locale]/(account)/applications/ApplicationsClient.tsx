"use client";

/**
 * The application draft, and the applications already raised.
 *
 * The draft at the top is not a form. Every field on it is an answer the citizen already
 * gave during onboarding, laid out in the order a Channel Partner's own form asks for
 * them, so the whole thing can be checked in one read before anyone walks to a counter.
 * Nothing here writes: `Submit` hands off to `/apply/[scheme]`, which is the real
 * submission path and the one a signed-out citizen uses too.
 *
 * The four steps across the top are read off actual state — profile completion, whether
 * the rule engine produced a verdict this citizen can act on, how many documents the
 * chosen scheme wants, and whether the draft is therefore ready. A row of green ticks
 * that is always green tells nobody anything, so a step that is not done says what is
 * missing.
 *
 * Each submitted row links to `/applications/[ref]`. That used to be `/track/[ref]`,
 * which a signed-out citizen reached by typing their reference number; there is one
 * signed-in journey now, and the list is the thing an account is actually for, since
 * remembering `SETU-2026-RJ-000031` is the part that fails.
 */

import {
  ArrowRight,
  Check,
  Download,
  FileText,
  MessageCircle,
  Send,
  ShieldCheck,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useMemo, useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import {
  ApplicationDraftSheet,
  type DraftSection,
} from "@/components/account/ApplicationDraftSheet";
import { DbtCheckDialog } from "@/components/account/DbtCheckDialog";
import { ShareOnWhatsAppDialog } from "@/components/account/ShareOnWhatsAppDialog";
import { useMatches, useMyApplications } from "@/components/account/useCitizenData";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";
import { schemeFact } from "@/lib/schemeFacts";

import type { Locale } from "@/i18n/config";

export function ApplicationsClient({ locale }: { locale: Locale }) {
  const t = useTranslations("myApplications");
  const tDraft = useTranslations("applicationDraft");
  const tCommon = useTranslations("common");

  const { account } = useAccount();
  const { data, loading } = useMyApplications();
  const matches = useMatches(locale);

  const [showWhatsApp, setShowWhatsApp] = useState(false);
  const [showDbt, setShowDbt] = useState(false);

  /** Stamped after mount, never during render — a `new Date()` in the render path is the
   *  non-deterministic value scripts/check-hydration.mjs fails the build for. */
  const [generatedAt, setGeneratedAt] = useState("");
  useEffect(() => {
    setGeneratedAt(
      new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date()),
    );
  }, [locale]);

  const applications = data ?? [];
  const profile = account?.profile;
  const dash = tCommon("notApplicable");
  const money = (value: number | null | undefined) =>
    value == null ? dash : tCommon("rupees", { amount: formatRupees(value, locale) });

  // The scheme the draft is for: the best match the citizen can actually have.
  const best =
    matches.data?.results.find((result) => result.verdict !== "INELIGIBLE") ?? null;
  const fit = best?.fit ? Math.round(best.fit.total) : null;

  /** Documents outstanding on the most recent application, which is the only real number
   *  this page has: the catalogue summary carries a rule count, not a document count, and
   *  using one for the other would put a wrong figure under a tick. */
  const latest = applications[0] ?? null;

  const location = [profile?.city, profile?.district, profile?.state]
    .filter(Boolean)
    .join(", ");

  /** The draft, as both the on-screen grid and the printed sheet read it. One source, so
   *  the page and the PDF cannot disagree. */
  const fields = [
    { label: tDraft("applicant"), value: profile?.display_name ?? dash },
    { label: tDraft("category"), value: profile?.category ?? dash },
    { label: tDraft("income"), value: money(profile?.annual_family_income) },
    { label: tDraft("enterprise"), value: profile?.business_name ?? dash },
    { label: tDraft("enterpriseType"), value: profile?.project_sector ?? dash },
    { label: tDraft("projectCost"), value: money(profile?.project_cost) },
    { label: tDraft("loanRequired"), value: money(profile?.loan_required) },
    { label: tDraft("location"), value: location || dash },
    { label: tDraft("preferredScheme"), value: best?.official_name ?? dash },
    {
      label: tDraft("preferredPartner"),
      value: schemeFact(best?.scheme_code ?? "")?.agency ?? dash,
    },
  ];

  /**
   * The four steps, from real state. A step that is not done says what is missing rather
   * than showing a tick nobody earned.
   */
  const completion = profile?.completion_pct ?? 0;
  const steps = [
    {
      key: "profile",
      done: completion >= 100,
      detail: completion >= 100 ? tDraft("done") : tDraft("percentDone", { pct: completion }),
    },
    {
      key: "eligibility",
      done: Boolean(best),
      detail: best ? tDraft("done") : tDraft("noVerdictYet"),
    },
    {
      key: "documents",
      done: latest !== null && latest.documents_outstanding === 0,
      detail:
        latest === null
          ? tDraft("afterSubmitting")
          : latest.documents_outstanding === 0
            ? tDraft("done")
            : tDraft("outstanding", { count: latest.documents_outstanding }),
    },
    {
      key: "draft",
      done: completion >= 100 && Boolean(best),
      detail: completion >= 100 && Boolean(best) ? tDraft("done") : tDraft("notReady"),
    },
  ];

  /** The three bands of the printed sheet. Picked by index rather than sliced, because
   *  location belongs with the enterprise and the two money figures do not. */
  const pick = (...indexes: number[]) => indexes.map((index) => fields[index]);
  const sections: DraftSection[] = [
    { heading: tDraft("sectionApplicant"), rows: pick(0, 1, 2) },
    { heading: tDraft("sectionEnterprise"), tone: "teal", rows: pick(3, 4, 7) },
    { heading: tDraft("sectionFinancing"), rows: pick(5, 6, 8, 9) },
  ];

  /** What goes to WhatsApp: what a partner needs at a counter, and nothing more. No
   *  Aadhaar, no bank details — this text leaves the app the moment it is shared. */
  const summary = useMemo(
    () =>
      [
        tDraft("summaryHeading"),
        "",
        ...fields.map((field) => `${field.label}: ${field.value}`),
        "",
        tDraft("sheetDisclaimer"),
      ].join("\n"),
    // `fields` is rebuilt every render; its content is the real dependency.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [JSON.stringify(fields)],
  );

  return (
    <div className="space-y-5">
      <header className="no-print">
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">
          {tDraft("heroTitle")}
        </h1>
        <p className="mt-1 text-ink-muted">{tDraft("heroSub")}</p>
      </header>

      <Card className="no-print">
        <CardContent className="grid gap-4 p-5 sm:grid-cols-2 lg:grid-cols-4 lg:p-6">
          {steps.map((step) => (
            <div key={step.key} className="flex items-center gap-3">
              <span
                aria-hidden="true"
                className={`grid h-8 w-8 shrink-0 place-items-center rounded-full ${
                  step.done ? "bg-good-bg text-good-fg" : "bg-canvas text-ink-faint"
                }`}
              >
                {step.done ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <span className="h-2 w-2 rounded-full bg-current" />
                )}
              </span>
              <span className="min-w-0">
                <span className="block font-semibold">{tDraft(`step.${step.key}`)}</span>
                <span className="block text-sm text-ink-faint">{step.detail}</span>
              </span>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card className="no-print">
        <CardContent className="p-5 lg:p-7">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                {tDraft("eyebrow")}
              </p>
              {/* Official name verbatim, never machine-translated (CLAUDE.md). */}
              <h2 className="mt-1.5 font-display text-xl font-extrabold" lang="en">
                {best?.official_name ?? tDraft("noSchemeYet")}
              </h2>
            </div>
            {fit !== null && (
              <Chip tone={fit >= 80 ? "good" : "accent"}>
                {tDraft("profileMatch", { pct: fit })}
              </Chip>
            )}
          </div>

          <dl className="mt-6 grid gap-x-8 gap-y-5 sm:grid-cols-2">
            {fields.map((field) => (
              <div key={field.label}>
                <dt className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                  {field.label}
                </dt>
                <dd className="mt-1 font-semibold tabular-nums">{field.value}</dd>
              </div>
            ))}
          </dl>

          <div className="mt-7 flex flex-wrap gap-2.5">
            <Button
              variant="secondary"
              onClick={() => setShowDbt(true)}
              className="rounded-full border-good-line text-base text-good-fg"
            >
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              {tDraft("dbtCheck")}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setShowWhatsApp(true)}
              className="rounded-full border-good-line text-base text-good-fg"
            >
              <MessageCircle className="h-4 w-4" aria-hidden="true" />
              {tDraft("shareWhatsApp")}
            </Button>
            {/* `window.print()` and not a PDF library — see ApplicationDraftSheet. */}
            <Button
              variant="secondary"
              onClick={() => window.print()}
              className="rounded-full text-base"
            >
              <Download className="h-4 w-4" aria-hidden="true" />
              {tDraft("downloadPdf")}
            </Button>
            {best && (
              <Link
                href={`/apply/${best.scheme_code}`}
                className="btn-primary rounded-full text-base"
              >
                <Send className="h-4 w-4" aria-hidden="true" />
                {tDraft("submit")}
              </Link>
            )}
          </div>
        </CardContent>
      </Card>

      <section className="no-print">
        <h2 className="font-display text-xl font-extrabold">{t("title")}</h2>

        {loading && !data ? (
          <p role="status" className="panel mt-3 p-8 text-center text-ink-faint">
            {tCommon("loading")}
          </p>
        ) : applications.length === 0 ? (
          <Card className="mt-3">
            <CardContent className="p-8 text-center">
              <FileText className="mx-auto h-8 w-8 text-ink-faint" aria-hidden="true" />
              <h3 className="mt-3 font-display text-lg font-bold">{t("emptyTitle")}</h3>
              <p className="mx-auto mt-2 max-w-md text-ink-muted">{t("emptyBody")}</p>
              <Link href="/matches" className="btn-primary mt-5">
                {t("startFromMatches")}
              </Link>
            </CardContent>
          </Card>
        ) : (
          <ul className="mt-3 space-y-3">
            {applications.map((application) => (
              <li key={application.reference_no}>
                <Card interactive>
                  <Link
                    href={`/applications/${application.reference_no}`}
                    className="flex items-center gap-4 p-5"
                  >
                    <span className="min-w-0 flex-1">
                      <span className="numeric block text-sm text-ink-faint">
                        {application.reference_no}
                      </span>
                      <span
                        className="mt-0.5 block font-display text-lg font-bold"
                        lang="en"
                      >
                        {application.scheme_name}
                      </span>
                    </span>
                    <Chip tone="warn">{application.status}</Chip>
                    <ArrowRight
                      className="h-4 w-4 shrink-0 text-ink-faint"
                      aria-hidden="true"
                    />
                  </Link>
                </Card>
              </li>
            ))}
          </ul>
        )}
      </section>

      <ShareOnWhatsAppDialog
        open={showWhatsApp}
        onOpenChange={setShowWhatsApp}
        summary={summary}
      />
      <DbtCheckDialog open={showDbt} onOpenChange={setShowDbt} />

      <ApplicationDraftSheet
        sections={sections}
        reference={null}
        scheme={best?.official_name ?? null}
        generatedAt={generatedAt}
      />
    </div>
  );
}
