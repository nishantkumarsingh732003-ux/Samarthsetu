import createMiddleware from "next-intl/middleware";

import { DEFAULT_LOCALE, LOCALES } from "./i18n/config";

export default createMiddleware({
  locales: LOCALES,
  defaultLocale: DEFAULT_LOCALE,
  // Always prefix. A citizen who shares a link shares the language they read it in.
  localePrefix: "always",
});

export const config = {
  // `.+` rather than `.*` so the bare "/" is NOT matched. That route is the language
  // picker and must render, rather than being redirected to a guessed locale — the
  // whole point of the screen is that the citizen chooses.
  matcher: ["/((?!api|_next|manifest\\.webmanifest|sw\\.js|icons|.*\\..*).+)"],
};
