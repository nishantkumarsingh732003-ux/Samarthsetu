import { getRequestConfig } from "next-intl/server";
import { notFound } from "next/navigation";

import { DEFAULT_LOCALE, isLocale } from "./config";

export default getRequestConfig(async ({ requestLocale }) => {
  // `requestLocale` is the current API; the older `locale` parameter is deprecated and
  // becomes an error in next-intl 4.
  const requested = await requestLocale;
  const locale = requested && isLocale(requested) ? requested : DEFAULT_LOCALE;

  if (requested && !isLocale(requested)) notFound();

  return {
    locale,
    messages: (await import(`../../messages/${locale}.json`)).default,
    timeZone: "Asia/Kolkata",
  };
});
