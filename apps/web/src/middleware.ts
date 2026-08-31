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
  // `console` and `demo` are excluded because neither is part of the citizen surface:
  // the consoles are English-only desk tools behind a login, and /demo is a pitch tool.
  // Rewriting either into /en/... would put them inside the localised citizen tree.
  matcher: ["/((?!api|_next|console|demo|manifest\\.webmanifest|sw\\.js|icons|.*\\..*).+)"],
};
