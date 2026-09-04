import createMiddleware from "next-intl/middleware";

import { DEFAULT_LOCALE, LOCALES } from "./i18n/config";

export default createMiddleware({
  locales: LOCALES,
  defaultLocale: DEFAULT_LOCALE,
  // Always prefix. A citizen who shares a link shares the language they read it in.
  localePrefix: "always",
  // `/` is redirected to the best match for the browser's Accept-Language, falling back
  // to English. This replaced a full-page picker: landing on a wall of six buttons
  // before seeing what the service *is* asked for a decision nobody had context for,
  // and every "change language" link bounced back to it and lost the citizen's place.
  // The choice now lives in the page furniture, on every screen — see
  // components/LanguageSwitcher.tsx — so detecting a starting point is safe rather than
  // a trap: a wrong guess is one control away from being corrected, in native script.
  localeDetection: true,
});

export const config = {
  // `.*`, so the bare "/" IS matched and redirects into a locale. It was `.+` to let the
  // language picker at "/" render; that page is gone and the redirect is the point.
  // `console` and `demo` are excluded because neither is part of the citizen surface:
  // the consoles are English-only desk tools behind a login, and /demo is a pitch tool.
  // Rewriting either into /en/... would put them inside the localised citizen tree.
  matcher: ["/((?!api|_next|console|demo|manifest\\.webmanifest|sw\\.js|icons|.*\\..*).*)"],
};
