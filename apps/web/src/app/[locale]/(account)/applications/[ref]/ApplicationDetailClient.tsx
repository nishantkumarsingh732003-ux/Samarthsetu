"use client";

/**
 * The signed-in frame around the tracking screen.
 *
 * `TrackClient` is the whole of it, so there is one implementation and this file is a
 * back link. Duplicating it so the two routes could diverge is exactly how a bug gets
 * fixed on one of them and not the other.
 *
 * The document list is on here. It used to be off, because `/track/[ref]` carried the
 * upload for a citizen with no account; that route went with the rest of the anonymous
 * journey, so this is the upload path for an application now. `/documents` remains a
 * checklist and says so.
 */

import { ArrowLeft } from "lucide-react";
import { useTranslations } from "next-intl";

import { TrackClient } from "@/components/account/TrackClient";
import { Link } from "@/i18n/navigation";

import type { Locale } from "@/i18n/config";

export function ApplicationDetailClient({
  locale,
  reference,
}: {
  locale: Locale;
  reference: string;
}) {
  const t = useTranslations("myApplications");

  return (
    <div className="space-y-4">
      <Link href="/applications" className="btn-quiet -ml-3 text-base">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" />
        {t("backToAll")}
      </Link>
      {/* Documents are shown here. They used to be suppressed because `/track/[ref]`
          carried the upload and this page was the status and timeline only; that route
          has been removed along with the rest of the anonymous journey, so this is now
          the upload path for an application. `/documents` is a checklist and says so. */}
      <TrackClient locale={locale} reference={reference} />
    </div>
  );
}
