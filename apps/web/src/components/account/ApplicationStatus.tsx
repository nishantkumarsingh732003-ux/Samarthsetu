"use client";

/**
 * Where one application has got to — the header card and the progress timeline.
 *
 * Rendered by `/applications/[ref]` inside the signed-in shell. It used to be shared with
 * `/track/[ref]`, which took no login so a citizen at a cyber cafe with a number on a
 * slip of paper could check; that route was removed with the rest of the anonymous
 * journey, and this is the one frame now.
 *
 * THE STAGES ARE THE REAL PIPELINE. `SUBMITTED → PARTNER_ACKNOWLEDGED → DOCS_REQUESTED →
 * UNDER_APPRAISAL → SANCTIONED → DISBURSED` is the status enum the API actually moves an
 * application through. The design drop drew a five-step strip that began with "Profile
 * Completed" — that is not a stage of an application, it is a stage of the applicant, and
 * putting it in the same row implies the office has done something it has not.
 *
 * Three states, as drawn: done is a green tick, the stage the application is *at* is an
 * amber clock, everything ahead is a grey ring. `stageState` below explains why that
 * comes from the application's position rather than from the audit trail. The rail is
 * green up to where the application actually is and grey beyond it — a rail that ran
 * green to a decision nobody has taken would be the cruellest thing on this page.
 */

import { Check, Clock } from "lucide-react";
import { useTranslations } from "next-intl";

import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";

import type { ApplicationResponse } from "@/lib/api";
import type { Locale } from "@/i18n/config";

/** The order the API moves an application through. Terminal refusals — REJECTED,
 *  WITHDRAWN — are not stages on this rail; they are said in the status chip instead,
 *  because drawing them as a step implies every application passes through them. */
const STAGES = [
  "SUBMITTED",
  "PARTNER_ACKNOWLEDGED",
  "DOCS_REQUESTED",
  "UNDER_APPRAISAL",
  "SANCTIONED",
  "DISBURSED",
] as const;

const STOPPED = new Set(["REJECTED", "WITHDRAWN"]);

export function ApplicationStatus({
  data,
  locale,
}: {
  data: ApplicationResponse;
  locale: Locale;
}) {
  const t = useTranslations("track");
  const tCommon = useTranslations("common");

  const stopped = STOPPED.has(data.status);

  /**
   * A stage's state comes from the application's *position* on the rail, not from whether
   * that individual transition appears in the audit trail.
   *
   * The trail is sparse — not every application has documents requested of it — so
   * filling dots straight from it leaves holes: an application under appraisal was
   * showing "Documents requested · not started" sitting between two completed stages,
   * which reads as a broken rail rather than as a step that was skipped. Position cannot
   * produce that, and "the application is past this point" is true of every stage behind
   * the current one.
   *
   * The current stage is amber and in progress, never a green tick. Ticking the stage an
   * application is sitting in is how a citizen concludes the office has finished with it.
   */
  const currentIndex = STAGES.indexOf(data.status as (typeof STAGES)[number]);
  const stageState = (index: number): "done" | "current" | "pending" => {
    // Refused or withdrawn: there is no current stage, only what actually happened.
    if (currentIndex === -1) {
      return new Set(data.timeline.map((entry) => entry.status)).has(STAGES[index])
        ? "done"
        : "pending";
    }
    if (index < currentIndex) return "done";
    return index === currentIndex ? "current" : "pending";
  };

  const created = data.submitted_at
    ? new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
        dateStyle: "medium",
      }).format(new Date(data.submitted_at))
    : tCommon("notApplicable");

  const facts = [
    { label: t("scheme"), value: data.scheme_name, lang: "en" },
    { label: t("partner"), value: data.partner?.name ?? tCommon("notApplicable") },
    { label: t("created"), value: created },
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="p-5 lg:p-7">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="min-w-0">
              <h1 className="font-display text-2xl font-extrabold lg:text-3xl">
                {t("statusTitle")}
              </h1>
              <p className="mt-1 text-ink-muted">
                {t("reference")}
                {" · "}
                {/* Large and selectable: this gets read aloud down a phone line. */}
                <span className="numeric select-all font-semibold text-ink">
                  {data.reference_no}
                </span>
              </p>
            </div>
            <Chip tone={stopped ? "stop" : "warn"} className="uppercase tracking-wide">
              {t(`status.${data.status}` as "status.SUBMITTED")}
            </Chip>
          </div>

          <dl className="mt-6 grid gap-5 sm:grid-cols-3">
            {facts.map((fact) => (
              <div key={fact.label}>
                <dt className="text-xs font-bold uppercase tracking-widest text-ink-faint">
                  {fact.label}
                </dt>
                <dd
                  className="mt-1 font-display text-lg font-bold tabular-nums"
                  lang={fact.lang}
                >
                  {fact.value}
                </dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-5 lg:p-7">
          <h2 className="font-display text-lg font-bold">{t("timelineTitle")}</h2>

          {/* A list to a screen reader, a rail to everyone else. `aria-current="step"`
              is what announces which stage the application is actually at. */}
          <ol className="mt-6 flex items-start overflow-x-auto pb-1">
            {STAGES.map((stage, index) => {
              const state = stageState(index);
              const done = state === "done";
              const current = state === "current";
              // The rail is green up to and including the stage the application sits in,
              // and grey beyond it.
              const railBefore = index <= currentIndex;
              const railAfter = index < currentIndex;

              return (
                <li
                  key={stage}
                  className="flex min-w-0 flex-1 flex-col items-center"
                  aria-current={current ? "step" : undefined}
                >
                  <div className="flex w-full items-center">
                    {/* Half-connectors either side of the dot, so the rail is continuous
                        without any element having to know its neighbour's width. */}
                    <span
                      aria-hidden="true"
                      className={`h-0.5 flex-1 ${
                        index === 0 ? "opacity-0" : railBefore ? "bg-good-fg" : "bg-line"
                      }`}
                    />
                    <span
                      aria-hidden="true"
                      className={`grid h-9 w-9 shrink-0 place-items-center rounded-full ${
                        done
                          ? "bg-good-bg text-good-fg"
                          : current
                            ? "bg-warn-bg text-warn-fg"
                            : "border-2 border-line bg-surface text-ink-faint"
                      }`}
                    >
                      {done ? (
                        <Check className="h-4 w-4" />
                      ) : current ? (
                        <Clock className="h-4 w-4" />
                      ) : null}
                    </span>
                    <span
                      aria-hidden="true"
                      className={`h-0.5 flex-1 ${
                        index === STAGES.length - 1
                          ? "opacity-0"
                          : railAfter
                            ? "bg-good-fg"
                            : "bg-line"
                      }`}
                    />
                  </div>

                  <span className="mt-2.5 px-1 text-center text-sm font-semibold">
                    {t(`status.${stage}` as "status.SUBMITTED")}
                  </span>
                  <span className="px-1 text-center text-sm text-ink-faint">
                    {done ? t("stageDone") : current ? t("stageNow") : t("stagePending")}
                  </span>
                </li>
              );
            })}
          </ol>

          {/* The line that keeps the rail honest. Nothing on this page is a decision. */}
          <p className="mt-6 border-t border-line pt-4 text-sm text-ink-faint">
            {t("indicativeOnly")}
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
