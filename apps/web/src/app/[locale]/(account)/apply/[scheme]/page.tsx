import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import { Suspense } from "react";

import { PageHeading } from "@/components/account/PageHeading";

import type { Locale } from "@/i18n/config";

import { ApplyClient } from "./ApplyClient";

/**
 * Raise an application against one scheme.
 *
 * Inside `(account)` — a route group, so the URL is still `/[locale]/apply/[scheme]` and
 * every link into it from the scheme page, the shortlist and the assistant keeps working.
 * What changed is the gate: this used to be reachable with no account, and the anonymous
 * journey it belonged to has been removed in favour of one signed-in path.
 */
export default async function Apply({
  params: { locale, scheme },
}: {
  params: { locale: Locale; scheme: string };
}) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <>
      <PageHeading
        title={t("apply.heading")}
        // Said before anything else on the page, because it is the single thing most
        // often misunderstood about this scheme: SamarthSetu does not lend.
        sub={t("apply.notALoan")}
        back={{ href: `/results/${scheme}/partners`, label: t("common.back") }}
      />
      <Suspense
        fallback={
          <div className="panel animate-pulse p-6" role="status">
            <div className="h-4 w-32 rounded-full bg-line" />
            <div className="mt-4 h-6 w-2/3 rounded-full bg-line" />
          </div>
        }
      >
        <ApplyClient locale={locale} schemeCode={scheme} />
      </Suspense>
    </>
  );
}
