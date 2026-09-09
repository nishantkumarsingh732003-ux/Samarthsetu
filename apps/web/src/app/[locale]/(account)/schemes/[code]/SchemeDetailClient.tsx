"use client";

/**
 * One scheme, all the way down, drawn to the SamarthSetu design drop.
 *
 * The shape the drop specifies: a header panel carrying the agency, the recommendation
 * and the profile-match score, the name with its gloss, a listen control and four stat
 * tiles; a tab strip; and a sticky bar at the foot that is always one tap from starting
 * an application.
 *
 * All six of the drop's tabs are here, plus Sources. The seventh is not padding: every
 * figure on this page has to carry `source_url`, `circular_ref`, `effective_from` and
 * `last_verified_on` (CLAUDE.md rule 2), and the open questions have to be as visible as
 * the answers. That has nowhere else to live, and dropping it to keep the tab count at
 * six would be trading a requirement for a pixel.
 *
 * What each tab is for:
 *
 *   Overview     what the scheme funds, who it is for, and on what terms — every figure
 *                interpolated from the rule pack, no editorial text
 *   Eligibility  one row per criterion: the citizen's own value against the requirement,
 *                then every rule with its condition printed verbatim. A verdict elsewhere
 *                in the app cites a rule id, and this is where anyone can read the rule
 *                carrying that id and check the arithmetic. An engine nobody can audit is
 *                indistinguishable from a model guessing — CLAUDE.md rule 1
 *   Benefits     what the scheme gives, then what the money actually costs, worked
 *                through at the scheme's own ceiling with `lib/emi`
 *   Documents    what to bring, one row each, opening to why it is wanted
 *   Partners     who is authorised to process this, which is the second half of the
 *                problem statement
 *   FAQ          the drop's three questions. The drop also supplied three answers, about
 *                collateral and processing times, that no source in this project
 *                supports. The questions are kept and answered from what the pack and the
 *                routing data actually say, including "not published" where that is the
 *                honest answer — invented policy on a ministry-branded page is worse than
 *                an unanswered question
 *   Sources      the provenance, with the open questions shown as prominently as the
 *                answers. A figure this project could not source is labelled, not rounded
 *                into confidence
 */

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Check,
  CircleHelp,
  FileText,
  MapPin,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAccount } from "@/components/account/AccountProvider";
import { criterionKey } from "@/components/account/criteriaLabels";
import { ShortlistButton } from "@/components/account/ShortlistButton";
import { useMatches } from "@/components/account/useCitizenData";
import { ReadAloud } from "@/components/ReadAloud";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Link } from "@/i18n/navigation";
import { routePartners, type RoutedPartner } from "@/lib/api";
import { getScheme } from "@/lib/citizenApi";
import { repaymentPlan } from "@/lib/emi";
import { formatRupees } from "@/lib/format";
import { isMoneyField, requirementFrom, type RequirementOp } from "@/lib/ruleRequirement";
import { schemeFact } from "@/lib/schemeFacts";

import type { CitizenProfile, SchemeDetail, SchemeRule } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

/** The tabs a `?tab=` value is allowed to name, in the order the strip draws them. The
 *  labels come from the catalogue below; this is the allowlist, so a hand-typed URL
 *  cannot land the page on a tab that does not exist. */
const TAB_IDS = [
  "overview",
  "eligibility",
  "benefits",
  "documents",
  "partners",
  "faq",
  "provenance",
] as const;

/** Per-family description. Every number in the sentence is interpolated from the scheme's
 *  own limits at render time — this supplies the grammar, never a figure. */
const FAMILY_DESCRIPTION: Record<string, string> = {
  MICRO_FINANCE: "descMicroFinance",
  TERM_LOAN: "descTermLoan",
  EDUCATION_LOAN: "descEducationLoan",
};

/** How a requirement operator reads. `matches.requirement.*` supplies the wording. */
const OP_KEY: Record<RequirementOp, string> = {
  eq: "reqIs",
  ne: "reqIsNot",
  lte: "reqUpTo",
  lt: "reqUnder",
  gte: "reqAtLeast",
  gt: "reqOver",
};

export function SchemeDetailClient({ locale, code }: { locale: Locale; code: string }) {
  const t = useTranslations("schemeDetail");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");

  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [missing, setMissing] = useState(false);
  const [partners, setPartners] = useState<RoutedPartner[] | null>(null);
  const matches = useMatches(locale);
  const { account } = useAccount();

  /**
   * The opening tab comes from `?tab=`, which is what makes "look at the documents tab"
   * a thing one person can send another — the reason `TabLinks` was built around links
   * in the first place. Selecting a tab after arrival stays client state: it is a view
   * change, not a navigation, and pushing history for it would turn Back into a tab
   * rewind. An unknown or absent value opens the overview.
   */
  const requestedTab = useSearchParams().get("tab");
  const [tab, setTab] = useState<string>(
    requestedTab && (TAB_IDS as readonly string[]).includes(requestedTab)
      ? requestedTab
      : "overview",
  );

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

  const district = account?.profile?.district ?? null;
  const ceiling = scheme?.limits.max_loan_amount ?? null;

  /**
   * The authorised partners, routed on the citizen's own district. Fetched once the
   * scheme has loaded because the request needs its ceiling as the ticket size, and
   * skipped entirely with no district — routing without an origin is a 422, and a tab
   * that says "tell us where you are" is better than one that says "server error".
   */
  useEffect(() => {
    if (!district || !ceiling) return;
    let cancelled = false;
    void routePartners({ schemeCode: code, amount: ceiling, district }).then((result) => {
      if (cancelled) return;
      setPartners(result.ok ? result.data.partners : []);
    });
    return () => {
      cancelled = true;
    };
  }, [code, district, ceiling]);

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
  const money = (value: number | null) =>
    value === null ? dash : tCommon("rupees", { amount: formatRupees(value, locale) });
  const months = (value: number | null) =>
    value === null ? t("notPublished") : tMatches("upToMonths", { count: value });
  const years = (value: number | null) =>
    value === null
      ? t("notPublished")
      : tMatches("upToYears", { years: Math.round(value / 12) });

  const rate =
    limits.interest_rate_min === null
      ? t("notPublished")
      : limits.interest_rate_min === limits.interest_rate_max
        ? tMatches("perYearFlat", { rate: limits.interest_rate_min })
        : tMatches("perYear", {
            min: limits.interest_rate_min,
            max: limits.interest_rate_max,
          });

  const fundingShare =
    limits.max_funding_pct === null ? t("notPublished") : `${limits.max_funding_pct}%`;

  /** The four the drop puts across the header. Money, cost, how long, and when the first
   *  instalment lands — the questions asked at the counter, in that order. */
  const tiles = [
    { label: t("maxFinancing"), value: money(limits.max_loan_amount) },
    { label: t("interestRate"), value: rate },
    { label: t("tenure"), value: years(limits.tenure_months) },
    { label: t("moratorium"), value: months(limits.moratorium_months) },
  ];

  const terms = [
    { label: t("maxLoan"), value: money(limits.max_loan_amount) },
    { label: t("maxProject"), value: money(limits.max_project_cost) },
    { label: t("fundingPct"), value: fundingShare },
    { label: t("interestBand"), value: rate },
    { label: t("tenureFull"), value: years(limits.tenure_months) },
    { label: t("moratorium"), value: months(limits.moratorium_months) },
  ];

  const requirements = scheme.rules.filter((rule) => rule.severity === "HARD_BLOCK");

  /** How a profile value reads on the row. `null` is not "no" — it is "not answered yet",
   *  and the row says so rather than implying a value the citizen never gave. */
  const profileValue = (field: string): string => {
    const raw = (account?.profile as CitizenProfile | undefined)?.[
      field as keyof CitizenProfile
    ];
    if (raw === null || raw === undefined) return t("notAnswered");
    if (typeof raw === "boolean") return raw ? t("yes") : t("no");
    if (typeof raw === "number") {
      return isMoneyField(field)
        ? tCommon("rupees", { amount: formatRupees(raw, locale) })
        : String(raw);
    }
    // Category and sector codes are shown verbatim — they are what the engine matched on
    // and what a partner's own form will ask for.
    return String(raw);
  };

  const requirementText = (rule: SchemeRule): string | null => {
    const requirement = requirementFrom(rule.when_source);
    if (!requirement) return null;
    const value =
      typeof requirement.value === "boolean"
        ? requirement.value
          ? t("yes")
          : t("no")
        : typeof requirement.value === "number" && isMoneyField(requirement.field)
          ? tCommon("rupees", { amount: formatRupees(requirement.value, locale) })
          : String(requirement.value);
    return t(OP_KEY[requirement.op], { value });
  };

  /**
   * One row per criterion, in rule order. The tick or cross comes from this citizen's own
   * match run, so a rule the engine has not been able to evaluate shows neither.
   *
   * Several rules can bear on one criterion — a Term Loan brackets project cost with a
   * floor and a ceiling — and the drop draws one row per criterion, not per rule. They
   * merge: the requirements join ("Over ₹1,40,000 · Up to ₹50,00,000", which is the band
   * stated as the two rules state it), and the row only ticks if every rule behind it
   * passed. Merging the other way round would tick a row that half failed.
   */
  const rows: {
    key: string;
    label: string;
    passed: boolean;
    failed: boolean;
    yours: string;
    required: string[];
    ruleIds: string[];
  }[] = [];

  for (const rule of requirements) {
    const key = criterionKey(rule.rule_id) ?? rule.rule_id;
    const passed = mine?.matched_because.some((r) => r.rule_id === rule.rule_id) ?? false;
    const failed = mine?.blocked_because.some((r) => r.rule_id === rule.rule_id) ?? false;
    const required = requirementText(rule);
    const existing = rows.find((row) => row.key === key);

    if (existing) {
      existing.passed = existing.passed && passed;
      existing.failed = existing.failed || failed;
      if (required && !existing.required.includes(required)) existing.required.push(required);
      existing.ruleIds.push(rule.rule_id);
      continue;
    }

    const field = rule.fields[0] ?? "";
    rows.push({
      key,
      label: criterionKey(rule.rule_id) ? t(`criterion.${key}`) : rule.message,
      passed,
      failed,
      yours: field ? profileValue(field) : dash,
      required: required ? [required] : [],
      ruleIds: [rule.rule_id],
    });
  }

  /**
   * A worked example at the scheme's own ceiling. Not a quote and not an offer: the
   * sanctioning partner sets the real terms, which the disclaimer under it says. It is
   * here because "8% a year over 7 years" means very little next to the instalment it
   * implies, and the citizen deserves to see that before walking into a branch.
   */
  const example =
    limits.max_loan_amount && limits.interest_rate_max && limits.tenure_months
      ? repaymentPlan(
          limits.max_loan_amount,
          limits.interest_rate_max,
          limits.tenure_months,
          limits.moratorium_months ?? 0,
        )
      : null;

  /** Reported turnaround across the partners actually authorised for this scheme. The FAQ
   *  answers "how long does approval take?" with this or with "not published" — never
   *  with a number nobody measured. */
  const turnarounds = (partners ?? [])
    .map((partner) => partner.avg_turnaround_days)
    .filter((days): days is number => days !== null);
  const averageTurnaround = turnarounds.length
    ? Math.round(turnarounds.reduce((sum, days) => sum + days, 0) / turnarounds.length)
    : null;

  const faqs = [
    {
      id: "collateral",
      question: t("faqCollateralQ"),
      answer: t("faqCollateralA"),
    },
    {
      id: "turnaround",
      question: t("faqTurnaroundQ"),
      answer:
        averageTurnaround === null
          ? t("faqTurnaroundUnknown")
          : t("faqTurnaroundA", {
              days: averageTurnaround,
              count: turnarounds.length,
            }),
    },
    { id: "multiple", question: t("faqMultipleQ"), answer: t("faqMultipleA") },
  ];

  const descriptionKey = FAMILY_DESCRIPTION[scheme.family];
  const agency = schemeFact(scheme.code)?.agency ?? null;
  const fitScore = mine?.fit ? Math.round(mine.fit.total) : null;

  /** Read aloud gets what the scheme is and who it is for — not the tables, which are
   *  read by eye and would take a minute of synthesised speech to no purpose. */
  const spoken = [
    scheme.official_name,
    descriptionKey ? t(descriptionKey, descriptionValues(limits)) : "",
    ...requirements.map((rule) => rule.message),
  ]
    .filter(Boolean)
    .join(" ");

  const tabs = [
    { id: "overview", label: t("tabOverview") },
    { id: "eligibility", label: t("tabEligibility") },
    { id: "benefits", label: t("tabBenefits") },
    { id: "documents", label: t("tabDocuments") },
    { id: "partners", label: t("tabPartners") },
    { id: "faq", label: t("tabFaq") },
    { id: "provenance", label: t("tabProvenance") },
  ];

  return (
    // Room at the foot for the sticky apply bar, so the last card is never under it.
    <div className="space-y-5 pb-28">
      <Link href="/schemes" className="btn-quiet -ml-3 text-base">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        {tCommon("back")}
      </Link>

      <header className="panel p-5 lg:p-7">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              {agency && <Chip tone="neutral">{agency}</Chip>}
              {mine?.rank === 1 && (
                <Chip tone="saffron" className="uppercase tracking-wide">
                  <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("recommended")}
                </Chip>
              )}
              {fitScore !== null && (
                <Chip tone={fitScore >= 80 ? "good" : fitScore >= 50 ? "accent" : "warn"}>
                  {tMatches("profileMatchPct", { pct: fitScore })}
                </Chip>
              )}
              {provenance.needs_verification && (
                <Chip tone="warn">
                  <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
                  {t("openQuestions")}
                </Chip>
              )}
            </div>

            {/* Official name verbatim, never machine-translated (CLAUDE.md). The gloss
                below it is the name in the reader's own script, so someone who has to say
                it at a counter knows how. It is absent on the English page because there
                the official name already is the reader's script. */}
            <h1 className="mt-3 font-display text-2xl font-extrabold lg:text-3xl" lang="en">
              {scheme.official_name}
            </h1>
            {scheme.name_gloss && (
              <p className="mt-1 text-lg text-ink-muted">{scheme.name_gloss}</p>
            )}
          </div>

          <div className="flex shrink-0 items-center gap-2.5">
            <ShortlistButton code={scheme.code} className="rounded-full" />
            <ReadAloud text={spoken} locale={locale} variant="full" />
          </div>
        </div>

        <dl className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {tiles.map((tile) => (
            <div key={tile.label} className="rounded-card bg-canvas p-4">
              <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-ink-faint">
                {tile.label}
              </dt>
              <dd className="mt-1.5 font-display text-lg font-extrabold tabular-nums">
                {tile.value}
              </dd>
            </div>
          ))}
        </dl>
      </header>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList aria-label={t("tabsLabel")}>
          {tabs.map((entry) => (
            <TabsTrigger key={entry.id} value={entry.id}>
              {entry.label}
            </TabsTrigger>
          ))}
        </TabsList>

      <TabsContent value="overview">
        <section className="panel space-y-6 p-5 lg:p-7">
          {descriptionKey && (
            <div>
              <h2 className="font-display text-lg font-bold">{t("description")}</h2>
              <p className="mt-2 text-ink-muted">
                {t(descriptionKey, descriptionValues(limits))}
              </p>
            </div>
          )}

          <div>
            <h2 className="font-display text-lg font-bold">{t("whoCanApply")}</h2>
            <ul className="mt-2 space-y-2">
              {requirements.map((rule) => (
                <li key={rule.rule_id} className="flex gap-2.5 text-ink-muted">
                  <span
                    aria-hidden="true"
                    className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent-600"
                  />
                  <span>
                    {rule.message}{" "}
                    <span className="numeric text-sm text-ink-faint">{rule.rule_id}</span>
                  </span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="font-display text-lg font-bold">{t("financialAssistance")}</h2>
            <dl className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {terms.map((term) => (
                <div key={term.label} className="rounded-card bg-canvas p-3">
                  <dt className="text-sm text-ink-faint">{term.label}</dt>
                  <dd className="mt-1 font-display font-bold tabular-nums">{term.value}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>
      </TabsContent>

      {/* One row per criterion, the citizen's own value against the requirement the rule
          states. Both halves are derived, not authored: the left from their profile, the
          right from the rule's published condition — see lib/ruleRequirement. */}
      <TabsContent value="eligibility">
        <div className="space-y-4">
          <section className="panel p-4 lg:p-5">
            <ul className="space-y-2.5">
              {rows.map((row) => (
                <li
                  key={row.key}
                  title={row.ruleIds.join(", ")}
                  className={`flex flex-wrap items-center justify-between gap-x-4 gap-y-1
                              rounded-card px-4 py-3 ${
                                row.failed
                                  ? "bg-stop-bg/60"
                                  : row.passed
                                    ? "bg-good-bg/60"
                                    : "bg-canvas"
                              }`}
                >
                  <span className="flex items-center gap-2.5 font-semibold">
                    {row.passed ? (
                      <Check className="h-4 w-4 shrink-0 text-good-fg" aria-hidden="true" />
                    ) : row.failed ? (
                      <X className="h-4 w-4 shrink-0 text-stop-fg" aria-hidden="true" />
                    ) : (
                      <span
                        aria-hidden="true"
                        className="h-4 w-4 shrink-0 rounded-full border-2 border-line"
                      />
                    )}
                    {row.label}
                  </span>
                  <span className="text-sm text-ink-muted">
                    {t("yourValue")}{" "}
                    <strong className="font-semibold text-ink">{row.yours}</strong>
                    {row.required.length > 0 && (
                      <>
                        {" · "}
                        {t("requiredValue")}{" "}
                        {/* Two rules can bracket one criterion — a floor and a ceiling —
                            and they read as the band they are: "Over X · Up to Y". */}
                        <strong className="font-semibold text-ink">
                          {row.required.join(" · ")}
                        </strong>
                      </>
                    )}
                  </span>
                </li>
              ))}
            </ul>
            {!mine && <p className="mt-3 px-4 text-ink-faint">{t("noRunYet")}</p>}
          </section>

          {/* The rules themselves, expression and all. This is the audit surface. */}
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
        </div>
      </TabsContent>

      <TabsContent value="benefits">
        <div className="space-y-4">
          <section className="panel p-4 lg:p-5">
            <dl className="grid gap-3 sm:grid-cols-2">
              {[
                { label: t("benefitInterest"), value: rate },
                { label: t("benefitFunding"), value: fundingShare },
                { label: t("moratorium"), value: months(limits.moratorium_months) },
                { label: t("tenure"), value: years(limits.tenure_months) },
              ].map((benefit) => (
                <div key={benefit.label} className="panel p-4">
                  <dt className="text-sm font-semibold text-teal-700">{benefit.label}</dt>
                  <dd className="mt-1 font-display text-lg font-bold tabular-nums">
                    {benefit.value}
                  </dd>
                </div>
              ))}
            </dl>
          </section>

          <section className="panel p-5 lg:p-7">
            <h2 className="font-display text-lg font-bold">{t("workedExample")}</h2>
            {example ? (
              <>
                <p className="mt-2 text-ink-muted">
                  {t("workedExampleIntro", {
                    amount: money(limits.max_loan_amount),
                    rate: String(limits.interest_rate_max),
                    years: Math.round((limits.tenure_months ?? 0) / 12),
                  })}
                </p>
                <dl className="mt-5 grid grid-cols-2 gap-3 lg:grid-cols-4">
                  {[
                    { label: t("monthlyEmi"), value: money(example.emi) },
                    { label: t("totalInterest"), value: money(example.totalInterest) },
                    { label: t("totalRepaid"), value: money(example.totalPayment) },
                    {
                      label: t("moratoriumInterest"),
                      value: money(example.moratoriumInterest),
                    },
                  ].map((row) => (
                    <div key={row.label} className="rounded-card bg-canvas p-4">
                      <dt className="text-xs font-bold uppercase leading-snug tracking-widest text-ink-faint">
                        {row.label}
                      </dt>
                      <dd className="mt-1.5 font-display text-lg font-extrabold tabular-nums">
                        {row.value}
                      </dd>
                    </div>
                  ))}
                </dl>
                <p className="mt-4 text-sm text-ink-faint">{t("exampleDisclaimer")}</p>
                <Link href="/calculator" className="btn-secondary mt-4 text-base">
                  {t("planThis")}
                </Link>
              </>
            ) : (
              <p className="mt-2 text-ink-muted">{t("noExample")}</p>
            )}
          </section>
        </div>
      </TabsContent>

      {/* One row per document, as the drop draws it. Each opens to why it is wanted, who
          issues it and how long it stays valid — and, where it carries a government ID,
          what happens to that ID (CLAUDE.md rule 4). Closed by default so the list stays
          a list. */}
      <TabsContent value="documents">
        <Card>
          <CardContent className="p-4 lg:p-5">
            <Accordion type="multiple" className="grid gap-3 lg:grid-cols-2">
              {scheme.required_documents.map((document) => (
                <AccordionItem key={document.id} value={document.id}>
                  <AccordionTrigger>
                    <FileText
                      className="h-4 w-4 shrink-0 text-accent-700"
                      aria-hidden="true"
                    />
                    {document.name}
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="text-ink-muted">{document.why}</p>
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
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
            <p className="mt-4 px-1 text-sm text-ink-faint">{t("documentsIntro")}</p>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="partners">
        <section className="panel p-4 lg:p-5">
          {!district ? (
            <p className="p-2 text-ink-muted">{t("partnersNeedDistrict")}</p>
          ) : partners === null ? (
            <p role="status" className="p-2 text-ink-faint">
              {tCommon("loading")}
            </p>
          ) : partners.length === 0 ? (
            <p className="p-2 text-ink-muted">{t("partnersNone")}</p>
          ) : (
            <ul className="grid gap-3 lg:grid-cols-2">
              {partners.map((partner) => (
                <li key={partner.partner_id} className="panel p-4">
                  <div className="flex gap-3">
                    <span
                      aria-hidden="true"
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-teal-50"
                    >
                      <MapPin className="h-4 w-4 text-teal-700" />
                    </span>
                    <div className="min-w-0">
                      <p className="font-display font-bold">{partner.name}</p>
                      <p className="text-ink-faint">
                        {[partner.district, partner.state].filter(Boolean).join(", ")}
                      </p>
                      <p className="mt-1 text-sm font-medium text-good-fg">
                        {t("acceptingApplications")}
                      </p>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="mt-4 px-1 text-ink-muted">{t("partnersIntro")}</p>
          <Link
            href={`/results/${scheme.code}/partners`}
            className="btn-primary mt-4 text-base"
          >
            {t("openPartners")}
            <ArrowRight className="h-4 w-4" aria-hidden="true" />
          </Link>
        </section>
      </TabsContent>

      <TabsContent value="faq">
        <Card>
          <CardContent className="p-4 lg:p-5">
            <Accordion type="multiple" className="space-y-3">
              {faqs.map((faq) => (
                <AccordionItem key={faq.id} value={faq.id}>
                  <AccordionTrigger>
                    <CircleHelp
                      className="h-4 w-4 shrink-0 text-accent-700"
                      aria-hidden="true"
                    />
                    {faq.question}
                  </AccordionTrigger>
                  <AccordionContent>
                    <p className="text-ink-muted">{faq.answer}</p>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="provenance">
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
        </TabsContent>
      </Tabs>

      {/* The apply bar the drop pins to the foot.
          `bottom-12` clears the phone's bottom nav, which is exactly `min-h-touch` (3rem)
          tall — see AppShell. At `lg` that nav is gone and the bar drops to the window
          edge, and `left-64` starts it where the sidebar ends: spanning the full width
          and padding the content across would lay an opaque strip over the sidebar's own
          last row, which is Sign out. */}
      <div className="fixed inset-x-0 bottom-12 z-20 border-t border-line bg-surface/95 px-4 py-3 backdrop-blur lg:bottom-0 lg:left-64 lg:px-7">
        <div className="mx-auto flex max-w-shell flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm text-ink-faint">{t("readyToApply")}</p>
            <p className="truncate font-display font-bold" lang="en">
              {scheme.official_name}
            </p>
          </div>
          {/* Both buttons side by side need 346px, which a 360px or 375px phone does not
              have once the bar's own padding is taken out — the primary was clipped at
              the right edge on the two commonest screen widths in India. Below `sm` the
              secondary steps aside and the primary takes the row: "Calculate EMI" is a
              duplicate of the link in the Benefits tab above and of the dashboard
              shortcut, and the one control that must never be half off screen is the one
              that starts the application. */}
          <div className="flex w-full shrink-0 gap-2 sm:w-auto">
            <Link href="/calculator" className="btn-secondary hidden text-base sm:inline-flex">
              {t("calculateEmi")}
            </Link>
            <Link
              href={`/apply/${scheme.code}`}
              className="btn-primary w-full justify-center text-base sm:w-auto"
            >
              {t("apply")}
              <ArrowRight className="h-4 w-4 shrink-0" aria-hidden="true" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

/** The placeholders every family description shares. Kept out of the component so the
 *  spoken string and the rendered one cannot drift apart. */
function descriptionValues(limits: SchemeDetail["limits"]) {
  return {
    pct: limits.max_funding_pct ?? 0,
    rate: limits.interest_rate_min ?? 0,
    amount: new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 }).format(
      limits.max_loan_amount ?? 0,
    ),
  };
}
