import { getTranslations, unstable_setRequestLocale } from "next-intl/server";
import { Suspense } from "react";

import { PageHeading } from "@/components/account/PageHeading";

import type { Locale } from "@/i18n/config";

import { PartnersClient } from "./PartnersClient";

/**
 * Which Channel Partners can actually process this scheme, nearest first.
 *
 * Inside `(account)` — a route group, so the URL stays `/[locale]/results/[scheme]/
 * partners` and the links into it from the scheme page, the shortlist and the assistant's
 * "Find a partner" action keep working. It is gated now rather than anonymous.
 *
 * Distinct from `/partners`, which is the coverage map across every scheme. This one
 * answers the second half of the problem statement: not "where are the partners" but
 * "which of them is authorised for *this* loan category, and which is nearest".
 */
export default async function Partners({
  params: { locale, scheme },
}: {
  params: { locale: Locale; scheme: string };
}) {
  unstable_setRequestLocale(locale);
  const t = await getTranslations();

  return (
    <>
      <PageHeading
        title={t("partners.heading")}
        sub={t("partners.nearbyExplainer")}
        back={{ href: "/matches", label: t("common.back") }}
      />
      <Suspense
        fallback={
          <div className="panel animate-pulse p-6" role="status">
            <div className="h-4 w-32 rounded-full bg-line" />
            <div className="mt-4 h-6 w-2/3 rounded-full bg-line" />
          </div>
        }
      >
        <PartnersClient locale={locale} schemeCode={scheme} />
      </Suspense>
    </>
  );
}
