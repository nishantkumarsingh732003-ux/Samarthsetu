"use client";

/**
 * The applications this citizen has raised.
 *
 * A convenience over the anonymous route, not a replacement for it: each row links to
 * `/track/[ref]`, the same page a signed-out citizen reaches by typing their reference
 * number. Nothing here is behind the account except the *list* — the thing an account is
 * actually for, since remembering `SETU-2026-RJ-000031` is the part that fails.
 *
 * The status word comes from the API, which localises it; the reference number is
 * rendered in tabular figures because it gets read aloud at a branch counter.
 */

import { ChevronRight, FileText } from "lucide-react";
import { useTranslations } from "next-intl";

import { useMyApplications } from "@/components/account/useCitizenData";
import { Chip } from "@/components/ui/controls";
import { Link } from "@/i18n/navigation";
import { formatRupees } from "@/lib/format";

import type { Locale } from "@/i18n/config";

export function ApplicationsClient({ locale }: { locale: Locale }) {
  const t = useTranslations("myApplications");
  const tCommon = useTranslations("common");
  const { data, loading } = useMyApplications();

  const applications = data ?? [];

  return (
    <div className="space-y-6">
      <header>
        <h1 className="font-display text-2xl font-extrabold lg:text-3xl">{t("title")}</h1>
        <p className="mt-1 text-ink-muted">{t("sub")}</p>
      </header>

      {loading && !data ? (
        <p role="status" className="panel p-8 text-center text-ink-faint">
          {tCommon("loading")}
        </p>
      ) : applications.length === 0 ? (
        <div className="panel p-8 text-center">
          <FileText className="mx-auto h-8 w-8 text-ink-faint" aria-hidden="true" />
          <h2 className="mt-3 font-display text-lg font-bold">{t("emptyTitle")}</h2>
          <p className="mx-auto mt-2 max-w-md text-ink-muted">{t("emptyBody")}</p>
          <Link href="/matches" className="btn-primary mt-5">
            {t("startFromMatches")}
          </Link>
        </div>
      ) : (
        <ul className="space-y-3">
          {applications.map((application) => (
            <li key={application.reference_no}>
              <Link href={`/track/${application.reference_no}`} className="panel-link p-5">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="numeric text-sm text-ink-faint">
                      {t("reference")} {application.reference_no}
                    </p>
                    {/* Official name verbatim (CLAUDE.md). */}
                    <h2 className="mt-1 font-display text-lg font-bold">
                      {application.scheme_name}
                    </h2>
                    <p className="mt-1 text-ink-muted">
                      {application.partner_name ?? t("noPartner")}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <Chip tone="accent">{application.status.replace(/_/g, " ")}</Chip>
                    <ChevronRight className="h-5 w-5 text-ink-faint" aria-hidden="true" />
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
                  {application.amount_requested !== null && (
                    <span className="numeric font-medium">
                      {formatRupees(application.amount_requested, locale)}
                    </span>
                  )}
                  {application.submitted_at && (
                    <span className="numeric text-ink-faint">
                      {t("submitted")} {application.submitted_at.slice(0, 10)}
                    </span>
                  )}
                  <span
                    className={
                      application.documents_outstanding > 0 ? "text-warn-fg" : "text-good-fg"
                    }
                  >
                    {application.documents_outstanding > 0
                      ? t("documentsOutstanding", { count: application.documents_outstanding })
                      : t("documentsComplete")}
                  </span>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
