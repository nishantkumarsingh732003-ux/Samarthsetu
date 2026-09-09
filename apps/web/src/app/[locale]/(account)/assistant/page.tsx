import { unstable_setRequestLocale } from "next-intl/server";

import { AssistantClient } from "@/app/[locale]/(account)/assistant/AssistantClient";

import type { Locale } from "@/i18n/config";

/**
 * Samarth AI inside the shell.
 *
 * Deliberately `/assistant` and not `/assist`. The anonymous `/assist` intake is a
 * different screen and stays where it is: it walks a signed-out citizen through the
 * smallest set of questions the engine needs, one at a time, and hands them to
 * `/results`. A route group does not change a URL, so the two cannot share a path — and
 * they should not, because they are different products for different people.
 */
export default function Assist({ params: { locale } }: { params: { locale: Locale } }) {
  unstable_setRequestLocale(locale);
  return <AssistantClient locale={locale} />;
}
