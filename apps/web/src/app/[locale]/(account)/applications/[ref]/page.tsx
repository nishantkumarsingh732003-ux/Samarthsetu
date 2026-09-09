import { unstable_setRequestLocale } from "next-intl/server";

import { ApplicationDetailClient } from "@/app/[locale]/(account)/applications/[ref]/ApplicationDetailClient";

import type { Locale } from "@/i18n/config";

/**
 * One application, inside the signed-in shell.
 *
 * The same status and the same document upload as `/track/[ref]`, which needs no login —
 * that route stays exactly where it is, because a citizen at a cyber cafe with a
 * reference number on a slip of paper is the case it was built for. This one exists so
 * that someone who *is* signed in does not get thrown out of the sidebar to read it.
 */
export default function ApplicationDetail({
  params: { locale, ref },
}: {
  params: { locale: Locale; ref: string };
}) {
  unstable_setRequestLocale(locale);
  return (
    <ApplicationDetailClient locale={locale} reference={decodeURIComponent(ref)} />
  );
}
