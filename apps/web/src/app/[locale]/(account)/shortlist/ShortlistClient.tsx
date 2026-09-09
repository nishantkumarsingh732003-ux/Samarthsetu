"use client";

/**
 * The schemes a citizen set aside, resolved fresh every time, drawn to the design drop.
 *
 * The device stores codes and only codes (see `lib/shortlist.ts`). Everything on this
 * page — the official name, the ceilings, the rate band — is looked up in the published
 * catalogue on load. Caching any of it against the bookmark would mean showing a citizen
 * a rate that was true when they saved it, which is the failure mode this whole product
 * exists to prevent.
 *
 * A code the catalogue no longer publishes is not silently dropped. It is listed as
 * withdrawn, because a scheme disappearing from under a saved bookmark is exactly the
 * kind of thing someone needs to be told rather than left to notice.
 *
 * THE REMINDER. Nothing in this app rings it. There is no scheduler and no push channel —
 * `/citizen/notifications` records messages the service already sent, it is not a queue
 * this page can add to. So the date is stored on the device and handed to the citizen's
 * own calendar as an .ics file, and the calendar does the reminding. The label under the
 * field says exactly that, because a date field that silently promised a notification
 * nobody would ever send is the worst kind of feature to put on a ministry-branded page.
 */

import { ArrowRight, Bell, Bookmark, CalendarPlus, Trash2 } from "lucide-react";
import { useTranslations } from "next-intl";

import { VerdictChip } from "@/components/account/MatchCard";
import { useCatalogue, useMatches } from "@/components/account/useCitizenData";
import { useReminders } from "@/components/account/useReminders";
import { useShortlist } from "@/components/account/useShortlist";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Chip } from "@/components/ui/controls";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";
import { calendarEvent, isCalendarDate } from "@/lib/reminders";
import { schemeFact } from "@/lib/schemeFacts";

import type { SchemeSummary } from "@/lib/citizenApi";
import type { Locale } from "@/i18n/config";

export function ShortlistClient({ locale }: { locale: Locale }) {
  const t = useTranslations("shortlist");
  const tCommon = useTranslations("common");
  const tMatches = useTranslations("matches");

  const { codes, ready, remove } = useShortlist();
  const reminders = useReminders();
  const catalogue = useCatalogue(locale);
  const matches = useMatches(locale);

  const bySchemeCode = new Map(
    (catalogue.data?.schemes ?? []).map((scheme) => [scheme.code, scheme]),
  );
  const verdictFor = new Map(
    (matches.data?.results ?? []).map((result) => [result.scheme_code, result]),
  );

  const dash = tCommon("notApplicable");
  const money = (amount: number | null | undefined) =>
    amount == null ? dash : tCommon("rupees", { amount: formatRupees(amount, locale) });

  /** The date as a citizen reads it — "9 Sep 2026", in their own locale and calendar. */
  const readable = (date: string) =>
    new Intl.DateTimeFormat(locale === "en" ? "en-IN" : `${locale}-IN`, {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(`${date}T00:00:00`));

  /**
   * Hand the date to whatever calendar the phone already has.
   *
   * Built and revoked on the device — no round trip, works offline, and the file carries
   * nothing the citizen did not already have in front of them. The UID is stable for a
   * scheme so re-saving updates the entry instead of adding a second one.
   */
  const addToCalendar = (scheme: SchemeSummary, date: string) => {
    const ics = calendarEvent({
      uid: `setu-${scheme.code}@samarthsetu`,
      date,
      title: t("calendarTitle", { scheme: scheme.official_name }),
      description: t("calendarBody", { scheme: scheme.official_name }),
      url: `${window.location.origin}/${locale}/schemes/${scheme.code}`,
    });
    const url = URL.createObjectURL(new Blob([ics], { type: "text/calendar" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${scheme.code.toLowerCase()}-reminder.ics`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-4">
      <header>
        <h1 className="flex items-center gap-2.5 font-display text-2xl font-extrabold lg:text-3xl">
          <Bookmark className="h-6 w-6 shrink-0 text-saffron" aria-hidden="true" />
          {t("title")}
        </h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      {!ready || (catalogue.loading && !catalogue.data) ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : codes.length === 0 ? (
        <Card>
          <CardContent className="p-8 text-center">
            <Bookmark className="mx-auto h-8 w-8 text-ink-faint" aria-hidden="true" />
            <h2 className="mt-3 font-display text-lg font-bold">{t("emptyTitle")}</h2>
            <p className="mx-auto mt-2 max-w-md text-ink-muted">{t("emptyBody")}</p>
            <Link href="/schemes" className="btn-primary mt-5">
              {t("browseSchemes")}
            </Link>
          </CardContent>
        </Card>
      ) : (
        <>
          <ul className="grid gap-3 lg:grid-cols-2">
            {codes.map((code) => {
              const scheme = bySchemeCode.get(code);
              const verdict = verdictFor.get(code);

              if (!scheme) {
                return (
                  <li key={code}>
                    <Card>
                      <CardContent className="flex items-start gap-3 p-5">
                        <div className="min-w-0 flex-1">
                          <p className="font-display font-bold">{t("withdrawnTitle")}</p>
                          <p className="numeric mt-1 text-sm text-ink-faint">{code}</p>
                          <p className="mt-2 text-ink-muted">{t("withdrawnBody")}</p>
                        </div>
                        <RemoveButton label={t("remove")} onClick={() => remove(code)} />
                      </CardContent>
                    </Card>
                  </li>
                );
              }

              const agency = schemeFact(code)?.agency ?? null;
              const date = reminders.get(code);
              const rate =
                scheme.limits.interest_rate_min == null
                  ? null
                  : scheme.limits.interest_rate_min === scheme.limits.interest_rate_max
                    ? tMatches("perYearFlat", { rate: scheme.limits.interest_rate_min })
                    : tMatches("perYear", {
                        min: scheme.limits.interest_rate_min,
                        max: scheme.limits.interest_rate_max ?? "",
                      });
              const tenure = scheme.limits.tenure_months
                ? tMatches("upToYears", {
                    years: Math.round(scheme.limits.tenure_months / 12),
                  })
                : null;

              return (
                <li key={code}>
                  <Card interactive className="h-full">
                    <CardContent className="flex h-full flex-col p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2">
                            {agency && <Chip tone="neutral">{agency}</Chip>}
                            {scheme.limits.max_loan_amount !== null && (
                              <Chip tone="good">
                                {t("upTo", {
                                  amount: money(scheme.limits.max_loan_amount),
                                })}
                              </Chip>
                            )}
                            {verdict && <VerdictChip verdict={verdict.verdict} />}
                          </div>
                          {/* Official name verbatim, never machine-translated. */}
                          <h2
                            className="mt-2.5 font-display text-lg font-bold"
                            lang="en"
                          >
                            {scheme.official_name}
                          </h2>
                          <p className="mt-0.5 text-sm text-ink-faint">
                            {[rate, tenure].filter(Boolean).join(" · ") || dash}
                          </p>
                        </div>
                        <RemoveButton label={t("remove")} onClick={() => remove(code)} />
                      </div>

                      <section className="mt-4 rounded-card border border-saffron-line bg-saffron-bg p-4">
                        <Label
                          htmlFor={`reminder-${code}`}
                          className="flex items-center gap-2 text-saffron-fg"
                        >
                          <Bell className="h-4 w-4 shrink-0" aria-hidden="true" />
                          {t("reminder")}
                        </Label>
                        <div className="mt-2 flex flex-wrap items-center gap-2">
                          <Input
                            id={`reminder-${code}`}
                            type="date"
                            value={date}
                            onChange={(event) =>
                              reminders.set(code, event.currentTarget.value)
                            }
                            className="min-w-0 flex-1 bg-surface"
                          />
                          {isCalendarDate(date) && (
                            <Button
                              variant="secondary"
                              onClick={() => addToCalendar(scheme, date)}
                              className="shrink-0 rounded-full border-saffron-line text-base text-saffron-fg"
                            >
                              <CalendarPlus className="h-4 w-4" aria-hidden="true" />
                              <span className="numeric">{readable(date)}</span>
                            </Button>
                          )}
                        </div>
                        {/* The one sentence that keeps this honest. */}
                        <p className="mt-2 text-sm text-saffron-fg">
                          {t("reminderHint")}
                        </p>
                      </section>

                      <div className="mt-5 grid gap-2.5 sm:grid-cols-2">
                        <Link
                          href={`/schemes/${code}`}
                          className="btn-secondary justify-center text-base"
                        >
                          {t("open")}
                        </Link>
                        <Link
                          href={`/results/${code}/partners`}
                          className="btn-primary justify-center text-base"
                        >
                          {t("apply")}
                          <ArrowRight className="h-4 w-4" aria-hidden="true" />
                        </Link>
                      </div>
                    </CardContent>
                  </Card>
                </li>
              );
            })}
          </ul>

        </>
      )}
    </div>
  );
}

function RemoveButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="shrink-0 rounded-full text-ink-faint hover:bg-stop-bg hover:text-stop-fg"
    >
      <Trash2 className="h-5 w-5" aria-hidden="true" />
    </Button>
  );
}
