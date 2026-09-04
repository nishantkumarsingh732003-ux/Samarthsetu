"use client";

/**
 * One scheme, all the way down: terms, every rule, the documents, and the sources.
 *
 * The Rules tab publishes each rule's expression verbatim — `profile.annual_family_income
 * > 500000` and so on. That is the point of the whole architecture: a verdict elsewhere
 * in the app cites a rule id, and this is where anyone can read the rule carrying that
 * id and check the arithmetic themselves. An eligibility engine nobody can audit is
 * indistinguishable from a model guessing, which is exactly what CLAUDE.md rule 1 rules
 * out.
 *
 * The Sources tab shows the open questions as prominently as the answers. A figure this
 * project could not source is labelled, not rounded into confidence.
 *
 * The design drop had an FAQ tab with three invented answers about collateral and
 * processing times. It is not ported: made-up policy on a ministry-branded page is worse
 * than a missing tab.
 */

import { AlertTriangle, ArrowLeft, ShieldAlert } from "lucide-react";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { useMatches } from "@/components/account/useCitizenData";
import { VerdictChip } from "@/components/account/MatchCard";
import { Chip } from "@/components/ui/controls";
import { TabLinks, TabPanel } from "@/components/ui/Panel";
import { Link } from "@/i18n/navigation";
import { getScheme } from "@/lib/citizenApi";
import { formatRupees } from "@/lib/format";

import type { SchemeDetail } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export function SchemeDetailClient({ locale, code }: { locale: Locale; code: string }) {
  const t = useTranslations("schemeDetail");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");

  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [tab, setTab] = useState("overview");
  const matches = useMatches(locale);

  useEffect(() => {
    let cancelled = false;
    void getScheme(code, locale).then((result) => {
      if (cancelled) return;
      if (result.ok) setScheme(result.data);
      else if (result.error === "notfound") setMissing(true);
    });
    return () => {
      cancelled = true;
    };
  }, [code, locale]);

  const mine = matches.data?.results.find((result) => result.scheme_code === code) ?? null;

  if (missing) {
    return (
      <p role="alert" className="panel p-8 text-center">
        {tCommon("error")}
      </p>
    );
  }
  if (!scheme) {
    return (
      <p role="status" className="panel p-8 text-center text-ink-faint">
        {tCommon("loading")}
      </p>
    );
  }

  const { limits, provenance } = scheme;
  const dash = tCommon("notApplicable");
  const money = (value: number | null) => (value === null ? dash : formatRupees(value, locale));
  const months = (value: number | null) =>
    value === null ? t("notPublished") : tMatches("months", { count: value });

  const terms = [
    { label: t("maxLoan"), value: money(limits.max_loan_amount) },
    { label: t("maxProject"), value: money(limits.max_project_cost) },
    {
      label: t("fundingPct"),
      value: limits.max_funding_pct === null ? t("notPublished") : `${limits.max_funding_pct}%`,
    },
    {
      label: t("interestBand"),
      value:
        limits.interest_rate_min === null
          ? t("notPublished")
          : limits.interest_rate_min === limits.interest_rate_max
            ? tMatches("perYearFlat", { rate: limits.interest_rate_min })
            : tMatches("perYear", {
                min: limits.interest_rate_min,
                max: limits.interest_rate_max,
              }),
    },
    { label: t("tenure"), value: months(limits.tenure_months) },
    { label: t("moratorium"), value: months(limits.moratorium_months) },
  ];

  const tabs = [
    { id: "overview", label: t("tabOverview") },
    { id: "rules", label: t("tabRules") },
    { id: "documents", label: t("tabDocuments") },
    { id: "provenance", label: t("tabProvenance") },
  ];

  return (
    <div className="space-y-6">
      <Link href="/schemes" className="btn-quiet -ml-3 text-base">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        {tCommon("back")}
      </Link>

      <header className="panel p-5 lg:p-7">
        <div className="flex flex-wrap items-center gap-2">
          <Chip tone="accent">{scheme.family.replace(/_/g, " ")}</Chip>
          {mine && <VerdictChip verdict={mine.verdict} />}
          {provenance.needs_verification && (
            <Chip tone="warn">
              <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
              {t("openQuestions")}
            </Chip>
          )}
        </div>
        <h1 className="mt-3 font-display text-2xl font-extrabold">{scheme.official_name}</h1>
        {scheme.name_gloss && <p className="mt-1 text-ink-muted">{scheme.name_gloss}</p>}

        <dl className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-3">
          {terms.map((term) => (
            <div key={term.label} className="rounded-card bg-canvas p-3">
              <dt className="text-sm text-ink-faint">{term.label}</dt>
              <dd className="numeric mt-1 font-display font-bold">{term.value}</dd>
            </div>
          ))}
        </dl>

        <div className="mt-6 flex flex-wrap gap-2">
          <Link href="/calculator" className="btn-secondary text-base">
            {t("planThis")}
          </Link>
          <Link href={`/results/${scheme.code}/partners`} className="btn-primary text-base">
            {t("openPartners")}
          </Link>
        </div>
        <p className="mt-3 text-sm text-ink-faint">
          {t("partnersHere", { count: scheme.authorised_partner_count })}
        </p>
      </header>

      <TabLinks tabs={tabs} current={tab} onSelect={setTab} label={t("tabsLabel")} />

      <TabPanel id="overview" current={tab}>
        {mine ? (
          <section className="panel p-5">
            <h2 className="font-display text-lg font-bold">{t("yourStanding")}</h2>
            <ul className="mt-3 space-y-2">
              {[...mine.matched_because, ...mine.blocked_because].map((reason) => (
                <li key={reason.rule_id} className="flex gap-2.5">
                  <span
                    aria-hidden="true"
                    className={
                      reason.severity === "HARD_BLOCK" ? "text-stop-fg" : "text-good-fg"
                    }
                  >
                    ●
                  </span>
                  <span>
                    {reason.message}{" "}
                    <span className="numeric text-sm text-ink-faint">{reason.rule_id}</span>
                  </span>
                </li>
              ))}
            </ul>
            {mine.missing_fields.length > 0 && (
              <p className="mt-4 rounded-card bg-warn-bg px-4 py-3 text-warn-fg">
                {tMatches("whatIsMissing")}: {mine.missing_fields.join(", ")}
              </p>
            )}
          </section>
        ) : (
          <p className="panel p-6 text-ink-muted">{tMatches("noResults")}</p>
        )}
      </TabPanel>

      <TabPanel id="rules" current={tab}>
        <ul className="space-y-3">
          {scheme.rules.map((rule) => (
            <li key={rule.rule_id} className="panel p-5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <span className="numeric font-semibold">{rule.rule_id}</span>
                <Chip tone={rule.severity === "HARD_BLOCK" ? "stop" : "warn"}>
                  {rule.severity === "HARD_BLOCK" ? t("hardBlock") : t("softWarn")}
                </Chip>
              </div>
              <p className="mt-2.5">{rule.message}</p>
              {rule.satisfied_message && (
                <p className="mt-1 text-good-fg">{rule.satisfied_message}</p>
              )}
              <pre className="numeric mt-3 overflow-x-auto rounded-card bg-canvas px-3 py-2 text-sm">
                <code>{rule.when_source}</code>
              </pre>
              <p className="mt-2 text-sm text-ink-faint">
                {t("reads", { fields: rule.fields.join(", ") })}
              </p>
              {rule.suggest_instead && (
                <p className="mt-2 text-accent-700">
                  {t("redirect", { scheme: rule.suggest_instead })}
                </p>
              )}
            </li>
          ))}
        </ul>
      </TabPanel>

      <TabPanel id="documents" current={tab}>
        <p className="text-ink-muted">{t("documentsIntro")}</p>
        <ul className="mt-4 grid gap-3 lg:grid-cols-2">
          {scheme.required_documents.map((document) => (
            <li key={document.id} className="panel p-5">
              <h3 className="font-display font-bold">{document.name}</h3>
              <p className="mt-1.5 text-ink-muted">{document.why}</p>
              <p className="mt-2 space-x-3 text-sm text-ink-faint">
                {document.issued_by && (
                  <span>{t("issuedBy", { authority: document.issued_by })}</span>
                )}
                {document.validity_months !== null && (
                  <span>{t("validity", { months: document.validity_months })}</span>
                )}
              </p>
              {document.validity_is_practice_not_rule && (
                <p className="mt-2 text-sm text-warn-fg">{t("validityPractice")}</p>
              )}
              {document.contains_government_id && (
                <p className="mt-2 flex items-start gap-2 rounded-card bg-accent-50 px-3 py-2 text-sm text-accent-800">
                  <ShieldAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
                  {t("containsGovId")}
                </p>
              )}
            </li>
          ))}
        </ul>
      </TabPanel>

      <TabPanel id="provenance" current={tab}>
        <section className="panel p-5">
          <dl className="grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="text-sm text-ink-faint">{t("sourceLabel")}</dt>
              <dd className="mt-1">
                {provenance.source_url ? (
                  <a
                    href={provenance.source_url}
                    className="text-accent-700 underline"
                    rel="noreferrer noopener"
                    target="_blank"
                  >
                    {provenance.source ?? provenance.source_url}
                  </a>
                ) : (
                  (provenance.source ?? dash)
                )}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-ink-faint">{t("circular")}</dt>
              <dd className="numeric mt-1">{provenance.circular_ref ?? t("notPublished")}</dd>
            </div>
            <div>
              <dt className="text-sm text-ink-faint">{t("effectiveFrom")}</dt>
              <dd className="numeric mt-1">
                {provenance.effective_from ?? t("notPublished")}
              </dd>
            </div>
            <div>
              <dt className="text-sm text-ink-faint">{t("lastVerified")}</dt>
              <dd className="numeric mt-1">{provenance.last_verified_on ?? dash}</dd>
            </div>
          </dl>

          {provenance.verification_note && (
            <p className="mt-5 border-t border-line pt-4 text-ink-muted">
              {provenance.verification_note}
            </p>
          )}
        </section>

        {provenance.open_questions.length > 0 && (
          <section className="panel mt-4 border-warn-line bg-warn-bg p-5">
            <h2 className="font-display text-lg font-bold text-warn-fg">
              {t("openQuestions")}
            </h2>
            <p className="mt-1 text-warn-fg">{t("openQuestionsIntro")}</p>
            <ul className="mt-3 space-y-2.5">
              {provenance.open_questions.map((question) => (
                <li key={question.field}>
                  <span className="numeric font-semibold text-warn-fg">{question.field}</span>
                  <p className="text-warn-fg">{question.question}</p>
                </li>
              ))}
            </ul>
          </section>
        )}
      </TabPanel>
    </div>
  );
}
