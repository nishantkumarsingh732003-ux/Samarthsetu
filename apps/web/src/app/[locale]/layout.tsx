import { NextIntlClientProvider } from "next-intl";
import { getMessages, unstable_setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { JudgeTour } from "@/components/JudgeTour";
import { OfflineBanner } from "@/components/OfflineBanner";
import { ChunkReloader } from "@/components/ChunkReloader";
import { ServiceWorker } from "@/components/ServiceWorker";
import { Toaster } from "@/components/ui/sonner";
import { LOCALES, isLocale, type Locale } from "@/i18n/config";
import { DISPLAY_PREFS_BOOT } from "@/lib/displayPrefs";

import { fontVariables } from "@/styles/fonts";

export function generateStaticParams() {
  return LOCALES.map((locale) => ({ locale }));
}

/**
 * The escape hatch, and the reason it is an inline script rather than a component.
 *
 * A service worker that serves a stale `/_next/static` chunk breaks the page *before* any
 * React code runs, so a cleanup written as a `useEffect` — which is what
 * `components/ServiceWorker.tsx` does — never executes. The thing that undoes a broken
 * worker cannot itself be delivered by the worker.
 *
 * This runs synchronously from the HTML, which navigations fetch network-first, so it is
 * always fresh even when every chunk behind it is stale. It unregisters, purges, and
 * reloads once — guarded on there actually being a registration, so it can never loop.
 *
 * Development only. In production the worker is the offline story and must stay.
 */
const KILL_STALE_WORKER = `
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.getRegistrations().then(function (rs) {
    if (!rs.length) return;
    Promise.all(rs.map(function (r) { return r.unregister(); }))
      .then(function () { return caches.keys(); })
      .then(function (ks) { return Promise.all(ks.map(function (k) { return caches.delete(k); })); })
      .then(function () { location.reload(); })
      .catch(function () {});
  }).catch(function () {});
}
`;

export default async function LocaleLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  if (!isLocale(locale)) notFound();
  unstable_setRequestLocale(locale as Locale);

  const messages = await getMessages();
  const isDevelopment = process.env.NODE_ENV !== "production";

  return (
    <html lang={locale} className={fontVariables}>
      <body className="min-h-screen antialiased">
        {/* Text size and contrast, applied before the first pixel. A `useEffect` would
            render the page at the wrong size and then jump — on every navigation, for
            the one citizen who most needed the setting. See lib/displayPrefs.ts. */}
        <script dangerouslySetInnerHTML={{ __html: DISPLAY_PREFS_BOOT }} />
        {isDevelopment && (
          <script dangerouslySetInnerHTML={{ __html: KILL_STALE_WORKER }} />
        )}
        <NextIntlClientProvider messages={messages}>
          <OfflineBanner />
          {children}
          {/* One toaster for the whole citizen surface. Mounted in the layout rather than
              per page so a toast raised just before a navigation is still on screen after
              it — which is the case that matters: "signed in" is worth reading on the
              page you land on, not the one you left. */}
          <Toaster />
          {/* Mounted for the whole localised tree, because the walkthrough navigates
              across it — landing, onboarding, matches, partners. Nothing but a storage
              read ships until a judge presses the button; see components/JudgeTour.tsx. */}
          <JudgeTour />
          <ChunkReloader />
          <ServiceWorker />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
