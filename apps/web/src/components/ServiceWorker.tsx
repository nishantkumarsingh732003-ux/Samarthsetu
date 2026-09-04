"use client";

import { useEffect } from "react";

/**
 * Registers the offline shell in production — and actively removes it in development.
 *
 * Deliberately tiny and hand-written rather than pulling in a PWA plugin: the whole point
 * of this route is a small bundle.
 *
 * The development branch is not tidiness, it is a bug fix. `next dev` serves
 * `/_next/static/chunks/webpack.js` with no content hash, so a service worker caching it
 * pins one build's webpack runtime against every later build's module graph. The symptom
 * is `TypeError: Cannot read properties of undefined (reading 'call')` from inside
 * webpack.js, on a dev server that is compiling and serving correctly, with nothing in
 * the logs and no obvious way to connect the two. A hard reload does not fix it, because
 * the worker answers before the network does.
 *
 * So in development we unregister every worker and delete every cache. That heals a
 * browser already in that state on its next load, rather than leaving someone to discover
 * `Application → Service Workers → Unregister` in devtools.
 *
 * Offline support is a production feature and is unaffected: `pnpm build && pnpm start`,
 * and the deployed app, register as before.
 */
export function ServiceWorker() {
  useEffect(() => {
    if (!("serviceWorker" in navigator)) return;

    if (process.env.NODE_ENV !== "production") {
      void navigator.serviceWorker.getRegistrations().then((registrations) => {
        for (const registration of registrations) {
          // Ask it to drop its caches before it goes, in case unregistering races the
          // last in-flight request it would otherwise answer from a stale entry.
          registration.active?.postMessage("setu:purge");
          void registration.unregister();
        }
      });
      if ("caches" in window) {
        void caches.keys().then((keys) => Promise.all(keys.map((key) => caches.delete(key))));
      }
      return;
    }

    navigator.serviceWorker.register("/sw.js").catch(() => {
      // An unregistered worker only costs offline support, never the page itself.
    });
  }, []);

  return null;
}
